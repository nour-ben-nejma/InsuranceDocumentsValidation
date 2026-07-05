#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/ocr/pipelines/carte_grise_pipeline.py

Pipeline d'extraction du certificat d'immatriculation (carte grise).
Utile pour la coherence avec le constat amiable : verifier que le
proprietaire declare (8. Assure) et le vehicule (9. Identite du Vehicule,
notamment N immatriculation) correspondent a la carte grise fournie.
"""

from PIL import Image

from app.ocr.inference import query_qwen
from app.ocr.prompts.carte_grise_prompts import PROMPT_CARTE_GRISE


def run_extraction_flow_carte_grise(image: Image.Image) -> tuple:
    """
    Une carte grise tient sur une seule zone dense (recto uniquement en
    general) : une resolution plus elevee aide a lire les petits champs
    (N de serie du type, CIN) sans avoir besoin de crops separes, comme
    on l'a fait pour le constat amiable.
    """
    parsed, raw, _ = query_qwen(
        image, PROMPT_CARTE_GRISE, max_tokens=280,
        resolution_limit=700, label="carte-grise"
    )
    return (parsed if parsed else {}), raw