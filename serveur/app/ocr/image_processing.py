#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/ocr/image_processing.py

Preprocessing image (CIN uniquement) + detection des cases cochees
du tableau "12. Circonstances" du constat amiable.

NE PAS utiliser preprocess_image_cv2 sur les crops du constat :
ca detruit le texte arabe manuscrit (voir commentaire dans constat_pipeline.py).
"""

from typing import List, Dict, Tuple
import time

import cv2
import numpy as np
from PIL import Image

# =====================================================================
# CONSTANTES CONSTAT
# =====================================================================
CIRCONSTANCES_MAP = {
    1: "en stationnement",
    2: "quittait un stationnement",
    3: "prenait un stationnement",
    4: "sortait d'un parking, d'un lieu prive, d'un chemin de terre",
    5: "s'engageait dans un parking, un lieu prive, un chemin de terre",
    6: "arret de circulation",
    7: "frottement sans changement de file",
    8: "heurtait a l'arriere, en roulant dans le meme sens et sur une meme file",
    9: "roulait dans le meme sens et sur une file differente",
    10: "changeait de file",
    11: "doublait",
    12: "virait a droite",
    13: "virait a gauche",
    14: "reculait",
    15: "empietait sur la partie de chaussee reservee a la circulation en sens inverse",
    16: "venait de droite (dans un carrefour)",
    17: "n'avait pas observe le signal de priorite",
}


# =====================================================================
# PREPROCESSING (CIN uniquement)
# =====================================================================
def preprocess_image_cv2(image: Image.Image) -> Image.Image:
    """Redressement + binarisation adaptative. Reserve a la CIN."""
    img_np = np.array(image.convert("L"))
    _, binary = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(binary > 0))
    if len(coords) > 100:
        angle = cv2.minAreaRect(coords)[-1]
        angle = -(90 + angle) if angle < -45 else -angle
        if abs(angle) < 5:
            h, w = img_np.shape
            M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            img_np = cv2.warpAffine(img_np, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    img_np = cv2.adaptiveThreshold(img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10)
    return Image.fromarray(img_np).convert("RGB")


def crop_card_region(image: Image.Image) -> Image.Image:
    """Detecte et recadre le contour de la carte d'identite dans l'image."""
    img_np = np.array(image)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return image
    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)
    ratio = w / h if h > 0 else 0
    if 1.3 <= ratio <= 1.9 and w > image.width * 0.4:
        m = 10
        return image.crop((max(0, x - m), max(0, y - m), min(image.width, x + w + m), min(image.height, y + h + m)))
    return image


# =====================================================================
# CONSTAT - DETECTION CASES COCHEES (image processing d'abord, VLM fallback)
# =====================================================================
def _detect_boxes_imageprocessing(image: Image.Image) -> Tuple[List[int], List[int]]:
    """
    Zones calibrees pour le crop circonstances 600x800 :
      - tableau_top = 12%, tableau_bottom = 70%
      - zone_a : colonnes 22%-31% (case vehicule A)
      - zone_b : colonnes 71%-80% (case vehicule B)
    """
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    img_h, img_w = img_cv.shape[:2]

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)

    tableau_top = int(img_h * 0.12)
    tableau_bottom = int(img_h * 0.70)
    line_height = (tableau_bottom - tableau_top) / 17.0

    scores_a, scores_b = [], []

    for line_num in range(1, 18):
        y1 = tableau_top + int((line_num - 1) * line_height)
        y2 = tableau_top + int(line_num * line_height)
        zone_a = thresh[y1:y2, int(img_w * 0.22):int(img_w * 0.31)]
        zone_b = thresh[y1:y2, int(img_w * 0.71):int(img_w * 0.80)]
        scores_a.append(cv2.countNonZero(zone_a))
        scores_b.append(cv2.countNonZero(zone_b))

    def detect_checked(scores, min_score: int = 40):
        arr = np.array(scores, dtype=float)
        threshold = arr.mean() + arr.std() * 0.5
        return [i + 1 for i, v in enumerate(arr) if v > threshold and v > min_score]

    boxes_a = detect_checked(scores_a)
    boxes_b = detect_checked(scores_b)

    print(f"  [IP] Scores A: {scores_a}")
    print(f"  [IP] Scores B: {scores_b}")
    print(f"  [IP] Detecte A={boxes_a}, B={boxes_b}")
    return boxes_a, boxes_b


def extract_checked_boxes(image: Image.Image, validate: bool = False) -> Tuple[List[int], List[int], Dict]:
    """
    Tente d'abord la detection par image processing (rapide, pas de GPU).
    Si rien n'est detecte, fallback sur le VLM (import local pour eviter
    une dependance circulaire avec inference.py).
    """
    print("[BOXES] Detection cases Vehicule A et B...")
    t0 = time.perf_counter()

    boxes_a, boxes_b = _detect_boxes_imageprocessing(image)

    if boxes_a or boxes_b:
        confidence = "high" if (boxes_a and boxes_b) else "medium"
        print(f"  OK Cases A: {boxes_a} | Cases B: {boxes_b} (Image Processing, {time.perf_counter()-t0:.2f}s)")
        return boxes_a, boxes_b, {"confidence": confidence, "method": "image_processing"}

    # Fallback VLM
    from app.ocr.inference import query_qwen  # import local: evite import circulaire

    print("  [BOXES] Image Processing vide -> fallback VLM...")
    prompt_detect = (
        'Analyse la section "12. circonstances" (17 lignes).\n'
        'Case GAUCHE = Vehicule A (fond jaune). Case DROITE = Vehicule B (fond bleu).\n'
        'Cochee = croix (X), trait (/) ou marque. Vide = rien.\n'
        'Reponds UNIQUEMENT avec ce JSON (17 entrees) :\n'
        '{"1":{"a":false,"b":false},"2":{"a":false,"b":false},"3":{"a":false,"b":false},'
        '"4":{"a":false,"b":false},"5":{"a":false,"b":false},"6":{"a":false,"b":false},'
        '"7":{"a":false,"b":false},"8":{"a":false,"b":false},"9":{"a":false,"b":false},'
        '"10":{"a":false,"b":false},"11":{"a":false,"b":false},"12":{"a":false,"b":false},'
        '"13":{"a":false,"b":false},"14":{"a":false,"b":false},"15":{"a":false,"b":false},'
        '"16":{"a":false,"b":false},"17":{"a":false,"b":false}}'
    )

    result, _, vlm_elapsed = query_qwen(image, prompt_detect, max_tokens=512,
                                         resolution_limit=512, label="circonstances-VLM")
    boxes_a, boxes_b = [], []
    if result:
        for key, val in result.items():
            try:
                num = int(key)
            except (TypeError, ValueError):
                continue
            if not (1 <= num <= 17) or not isinstance(val, dict):
                continue
            if bool(val.get("a")):
                boxes_a.append(num)
            if bool(val.get("b")):
                boxes_b.append(num)
        boxes_a = sorted(set(boxes_a))
        boxes_b = sorted(set(boxes_b))

    confidence = "high" if (boxes_a or boxes_b) else "low"
    print(f"  OK Cases A: {boxes_a} | Cases B: {boxes_b} (VLM fallback, {time.perf_counter()-t0:.2f}s)")
    return boxes_a, boxes_b, {"confidence": confidence, "method": "vlm"}


def resolve_circonstances(checked_rows_a: list, checked_rows_b: list) -> dict:
    return {
        "12. Circonstances": {
            "Vehicule A": [CIRCONSTANCES_MAP.get(int(i), f"Item {i}") for i in checked_rows_a],
            "Vehicule B": [CIRCONSTANCES_MAP.get(int(i), f"Item {i}") for i in checked_rows_b],
        }
    }