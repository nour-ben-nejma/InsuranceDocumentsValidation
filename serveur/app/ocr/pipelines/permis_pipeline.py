#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/ocr/pipelines/permis_pipeline.py

Pipeline d'extraction du permis de conduire tunisien.
Utile pour la coherence avec le constat amiable : le "Permis de conduire N"
et le nom/prenom du conducteur (7. Identite du Conducteur) doivent
correspondre a ce document si l'agent le demande en piece complementaire.
"""

from PIL import Image

from app.ocr.inference import query_qwen
from app.ocr.image_processing import crop_card_region
from app.ocr.prompts.permis_prompts import PROMPT_PERMIS


def run_extraction_flow_permis(image: Image.Image) -> tuple:
    """
    Meme format physique qu'une CIN (carte rigide/plastifiee) -> on reutilise
    crop_card_region pour isoler la carte du fond (main, table, etc.) avant
    extraction, comme pour la CIN.
    """
    image_cropped = crop_card_region(image)
    parsed, raw, _ = query_qwen(
        image_cropped, PROMPT_PERMIS, max_tokens=280,
        resolution_limit=600, label="permis"
    )
    return (parsed if parsed else {}), raw