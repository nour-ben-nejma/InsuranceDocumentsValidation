#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/ocr/inference.py

Fonctions bas niveau d'appel au modele Qwen2.5-VL (query_qwen, query_qwen_batch)
et parsing JSON de sortie (extract_json).

Le modele/processor ne sont JAMAIS charges ici : ils viennent du ModelManager
singleton (app/core/model_loader.py), deja charge au demarrage du serveur.
"""

import re
import json
import time
from typing import Dict, List, Optional

import torch
from PIL import Image
from qwen_vl_utils import process_vision_info

from app.core.model_loader import get_model_and_processor
from app.ocr.image_processing import preprocess_image_cv2

_FENCE_RE = re.compile(r"[`]{3}(?:json)?\s*(.*?)\s*[`]{3}", re.DOTALL)


def extract_json(text: str) -> Optional[Dict]:
    """Extrait un objet JSON depuis la sortie brute du modele (avec ou sans fences)."""
    m = _FENCE_RE.search(text)
    candidate = m.group(1) if m else text.strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        print(f"    [EXTRACT_JSON] Fence parse failed: {e}")

    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError as e:
            print(f"    [EXTRACT_JSON] Bracket parse failed: {e}")

    print("    [EXTRACT_JSON] No valid JSON found in text")
    return None


def query_qwen(image: Image.Image,
                prompt: str,
                max_tokens: int = 512,
                with_preprocessing: bool = False,
                resolution_limit: int = 512,
                label: str = "") -> tuple:
    """
    Appel unique au VLM sur une seule image.
    Retourne (parsed_dict_or_None, raw_str, elapsed_seconds).
    """
    model, processor = get_model_and_processor()

    if with_preprocessing:
        image = preprocess_image_cv2(image)

    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": image,
             "min_pixels": 256 * 256, "max_pixels": resolution_limit * resolution_limit},
            {"type": "text", "text": prompt},
        ]
    }]

    def _generate(msgs):
        tpl = processor.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        img_in, vid_in = process_vision_info(msgs)
        inputs = processor(text=[tpl], images=img_in, videos=vid_in, padding=True, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        with torch.inference_mode():
            gen_ids = model.generate(**inputs, max_new_tokens=max_tokens,
                                      do_sample=False, use_cache=True,
                                      eos_token_id=processor.tokenizer.eos_token_id)
        trimmed = [out[len(inp):] for inp, out in zip(inputs["input_ids"], gen_ids)]
        raw = processor.batch_decode(trimmed, skip_special_tokens=True,
                                      clean_up_tokenization_spaces=False)[0]
        del inputs, gen_ids, trimmed
        torch.cuda.empty_cache()
        return raw

    t0 = time.perf_counter()
    raw = _generate(messages)
    elapsed = time.perf_counter() - t0
    parsed = extract_json(raw)

    print(f"\n[DEBUG {label}]")
    print(f"  RAW OUTPUT ({len(raw)} chars): {raw[:300]}..." if len(raw) > 300 else f"  RAW OUTPUT: {raw}")
    print(f"  PARSED: {parsed}")
    print(f"  ELAPSED: {elapsed:.2f}s")

    if parsed is None:
        print(f"  [RETRY] {label} - JSON invalide, retry...")
        messages[0]["content"][1]["text"] += "\n\nIMPORTANT: JSON brut uniquement, aucun texte."
        t0 = time.perf_counter()
        raw = _generate(messages)
        elapsed += time.perf_counter() - t0
        parsed = extract_json(raw)
        print(f"  [RETRY RESULT] PARSED: {parsed}")

    if label:
        print(f"  [TIMING] {label}: {elapsed:.2f}s")

    return parsed, raw, elapsed


def query_qwen_batch(images: list,
                      prompts: list,
                      max_tokens: int = 320,
                      resolution_limit: int = 600,
                      labels: list = None) -> list:
    """
    Traite plusieurs images en UN SEUL appel model.generate() (batch GPU natif).

    A UTILISER pour vehicule A + B du constat au lieu de deux appels
    query_qwen() sequentiels : evite la contention CUDA sur le modele 4-bit
    et reduit la latence totale, important sur une RTX 4060 8GB.

    Retourne une liste de tuples (parsed_dict_or_None, raw_str, elapsed_seconds),
    dans le meme ordre que images/prompts.
    """
    model, processor = get_model_and_processor()
    labels = labels or [""] * len(images)

    messages_list = [
        [{
            "role": "user",
            "content": [
                {"type": "image", "image": img,
                 "min_pixels": 256 * 256, "max_pixels": resolution_limit * resolution_limit},
                {"type": "text", "text": prompt},
            ]
        }]
        for img, prompt in zip(images, prompts)
    ]

    templates = [processor.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
                 for m in messages_list]

    all_images, all_videos = [], []
    for m in messages_list:
        imgs, vids = process_vision_info(m)
        all_images.extend(imgs)
        if vids:
            all_videos.extend(vids)

    inputs = processor(text=templates, images=all_images,
                        videos=all_videos or None, padding=True, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    t0 = time.perf_counter()
    with torch.inference_mode():
        gen_ids = model.generate(**inputs, max_new_tokens=max_tokens,
                                  do_sample=False, use_cache=True,
                                  eos_token_id=processor.tokenizer.eos_token_id)
    elapsed_total = time.perf_counter() - t0

    trimmed = [out[len(inp):] for inp, out in zip(inputs["input_ids"], gen_ids)]
    raws = processor.batch_decode(trimmed, skip_special_tokens=True,
                                   clean_up_tokenization_spaces=False)

    del inputs, gen_ids, trimmed
    torch.cuda.empty_cache()

    results = []
    for raw, label in zip(raws, labels):
        parsed = extract_json(raw)
        print(f"\n[DEBUG {label}]")
        print(f"  RAW OUTPUT ({len(raw)} chars): {raw[:300]}..." if len(raw) > 300 else f"  RAW OUTPUT: {raw}")
        print(f"  PARSED: {parsed}")
        if parsed is None:
            print(f"  [WARN] {label} - JSON invalide dans le batch (pas de retry individuel en mode batch)")
        results.append((parsed, raw, elapsed_total / len(images)))

    if labels and any(labels):
        print(f"  [TIMING] batch({'+'.join(l for l in labels if l)}): {elapsed_total:.2f}s total "
              f"({elapsed_total/len(images):.2f}s/image moyenne)")

    return results