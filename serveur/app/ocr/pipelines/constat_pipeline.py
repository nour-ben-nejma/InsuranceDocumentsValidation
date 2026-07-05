#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/ocr/pipelines/constat_pipeline.py

Pipeline d'extraction complet du constat amiable :
header, vehicule A/B, circonstances (cases cochees), signatures.

Historique des tentatives sur vehicule A/B (pour memoire, ne pas repeter) :
  - batch GPU natif a 600px  -> depassement VRAM silencieux (fallback
    memoire systeme Windows), latence x500 (1071s au lieu de 25s).
  - sequentiel a 448px       -> latence correcte (25s) mais precision
    degradee (champs merges, plaque erronee).
  - sequentiel a 512px       -> toujours des erreurs de lecture.
  - double extraction        -> INUTILE ici : le decodage est deterministe
    (do_sample=False), donc 2 appels sur le meme crop redonnent quasi
    toujours la meme reponse, meme fausse. Ca ne detecte que l'instabilite
    aleatoire du modele, pas les erreurs systematiques liees a la resolution.
  - RETENU : sequentiel a 600px + double quantization (model_loader.py)
    + torch.cuda.empty_cache() entre A et B + fermeture des apps qui
    consomment de la VRAM en arriere-plan (navigateur, Discord...).
"""

import time
from typing import Dict, Optional

import torch
from PIL import Image

from app.ocr.inference import query_qwen
from app.ocr.image_processing import extract_checked_boxes
from app.ocr.prompts.constat_prompts import PROMPT_HEADER, PROMPT_SIGNATURE, make_prompt_vehicule


def _safe_get(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, {})
    return d if d != {} else default


def run_extraction_flow_constat_complete(image: Image.Image) -> tuple:
    width, height = image.size
    timings = {}

    def resize_crop(crop, tw, th):
        return crop.resize((tw, th), Image.Resampling.LANCZOS)

    # --- CROPS ---
    header_crop = image.crop((0, 0, width, int(height * 0.22)))
    if max(header_crop.size) > 768:
        header_crop.thumbnail((768, 768), Image.Resampling.LANCZOS)

    vehicule_a_crop = resize_crop(
        image.crop((0, int(height * 0.20), int(width * 0.45), int(height * 0.75))), 600, 600
    )
    vehicule_b_crop = resize_crop(
        image.crop((int(width * 0.55), int(height * 0.20), width, int(height * 0.75))), 600, 600
    )
    circonstances_crop = resize_crop(
        image.crop((int(width * 0.25), int(height * 0.18), int(width * 0.75), int(height * 0.87))), 600, 800
    )

    sig_a_crop = image.crop((0, int(height * 0.90), int(width * 0.50), height))
    sig_b_crop = image.crop((int(width * 0.50), int(height * 0.90), width, height))
    for c in [sig_a_crop, sig_b_crop]:
        if max(c.size) > 512:
            c.thumbnail((512, 512), Image.Resampling.LANCZOS)

    # --- HEADER ---
    print("[INFERENCE] Header...")
    parsed_header, raw_header, t = query_qwen(
        header_crop, PROMPT_HEADER, max_tokens=60, resolution_limit=512, label="header"
    )
    timings["header"] = t

    # --- VEHICULE A + B : sequentiel a 600px, cache vide entre les deux ---
    print("[INFERENCE] Vehicule A + B (sequentiel, 600px, cache vide entre les deux)...")
    t_veh = time.perf_counter()
    parsed_a, raw_a, ta = query_qwen(
        vehicule_a_crop, make_prompt_vehicule("A"),
        max_tokens=320, resolution_limit=600, label="veh-A"
    )
    torch.cuda.empty_cache()
    parsed_b, raw_b, tb = query_qwen(
        vehicule_b_crop, make_prompt_vehicule("B"),
        max_tokens=320, resolution_limit=600, label="veh-B"
    )
    torch.cuda.empty_cache()
    timings["veh_batch"] = time.perf_counter() - t_veh
    print(f"  OK VEH_A + VEH_B sequentiel 600px: {timings['veh_batch']:.1f}s")

    # --- CIRCONSTANCES ---
    print("[INFERENCE] Circonstances...")
    t0 = time.perf_counter()
    boxes_a, boxes_b, meta = extract_checked_boxes(circonstances_crop, validate=False)
    timings["circonstances"] = time.perf_counter() - t0

    # --- SIGNATURES ---
    print("[INFERENCE] Signatures...")
    t0 = time.perf_counter()
    parsed_sig_a, raw_sig_a, _ = query_qwen(sig_a_crop, PROMPT_SIGNATURE, max_tokens=16,
                                             resolution_limit=384, label="sig-A")
    parsed_sig_b, raw_sig_b, _ = query_qwen(sig_b_crop, PROMPT_SIGNATURE, max_tokens=16,
                                             resolution_limit=384, label="sig-B")
    timings["signatures"] = time.perf_counter() - t0

    sig_a_present = bool(parsed_sig_a.get("signed", False)) if parsed_sig_a else False
    sig_b_present = bool(parsed_sig_b.get("signed", False)) if parsed_sig_b else False

    complete_json = {
        "1. Date et Lieu": {
            "Date": _safe_get(parsed_header, "Date") if parsed_header else None,
            "Lieu": _safe_get(parsed_header, "Lieu") if parsed_header else None,
        },
        "6. Societe d Assurances": {
            "Vehicule A": _safe_get(parsed_a, "6. Societe d Assurances") if parsed_a else {},
            "Vehicule B": _safe_get(parsed_b, "6. Societe d Assurances") if parsed_b else {},
        },
        "7. Identite du Conducteur": {
            "Vehicule A": _safe_get(parsed_a, "7. Identite du Conducteur") if parsed_a else {},
            "Vehicule B": _safe_get(parsed_b, "7. Identite du Conducteur") if parsed_b else {},
        },
        "8. Assure": {
            "Vehicule A": _safe_get(parsed_a, "8. Assure") if parsed_a else {},
            "Vehicule B": _safe_get(parsed_b, "8. Assure") if parsed_b else {},
        },
        "9. Identite du Vehicule": {
            "Vehicule A": _safe_get(parsed_a, "9. Identite du Vehicule") if parsed_a else {},
            "Vehicule B": _safe_get(parsed_b, "9. Identite du Vehicule") if parsed_b else {},
        },
        "12. Circonstances": {
            "Vehicule A": boxes_a,
            "Vehicule B": boxes_b,
        },
        "Signature": {
            "Vehicule A Presente": sig_a_present,
            "Vehicule B Presente": sig_b_present,
        },
    }

    total = sum(timings.values())
    print("\n" + "-" * 50)
    print("TIMING PAR ETAPE :")
    for k, v in timings.items():
        print(f"   {k:<25} {v:.2f}s")
    print(f"   {'TOTAL':<25} {total:.2f}s")
    print("-" * 50)

    raw_backup = (
        f"[HEADER] {raw_header}\n"
        f"[VEH-A]  {raw_a}\n"
        f"[VEH-B]  {raw_b}\n"
        f"[SIG-A]  {raw_sig_a}\n"
        f"[SIG-B]  {raw_sig_b}\n"
    )

    return complete_json, raw_backup, timings