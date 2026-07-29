#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/ocr/pipelines/attestation_pipeline.py
"""

import re
from PIL import Image
from app.ocr.inference import query_qwen
from app.ocr.prompts.attestation_prompts import PROMPT_ATTESTATION


def _normalize_immatriculation(immat: str) -> str:
    """
    Normalise la plaque d'immatriculation tunisienne :
    - "216 تونس 7182"  -> "216 TUN 7182"
    - "216تونس7182"    -> "216 TUN 7182"
    - "216 TUN 7182"   -> "216 TUN 7182" (inchange)
    """
    if not immat:
        return immat
    # Remplacer le mot arabe تونس par TUN
    normalized = re.sub(r"\s*تونس\s*", " TUN ", immat.strip())
    # Nettoyer les espaces multiples
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def run_extraction_flow_attestation(image: Image.Image) -> tuple:
    """
    Extrait les donnees d'une attestation d'assurance tunisienne.
    """
    parsed, raw, _ = query_qwen(
        image, PROMPT_ATTESTATION, max_tokens=400,
        resolution_limit=900, label="attestation"
    )

    if parsed:
        # Normaliser la plaque d'immatriculation (تونس -> TUN)
        if parsed.get("immatriculation"):
            parsed["immatriculation"] = _normalize_immatriculation(
                str(parsed["immatriculation"])
            )
        # Ajouter la marque/type au champ de schema route
        # (le router_pipeline les encapsule dans {"value": ...})

    return (parsed if parsed else {}), raw
