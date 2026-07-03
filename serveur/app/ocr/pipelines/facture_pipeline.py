#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/ocr/pipelines/facture_pipeline.py

Pipeline d'extraction de la facture de reparation.
"""

from PIL import Image

from app.ocr.inference import query_qwen
from app.ocr.prompts.facture_prompts import PROMPT_FACTURE


def run_extraction_flow_facture(image: Image.Image) -> tuple:
    parsed, raw, _ = query_qwen(
        image, PROMPT_FACTURE, max_tokens=350, resolution_limit=768, label="facture"
    )
    fields = parsed if parsed else {}
    if "is_signed" in fields:
        val = fields["is_signed"]
        fields["is_signed"] = (
            ("oui" in str(val).lower() or "true" in str(val).lower())
            if isinstance(val, str) else bool(val)
        )
    return fields, raw