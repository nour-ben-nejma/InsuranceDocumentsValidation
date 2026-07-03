#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/ocr/pipelines/cin_pipeline.py

Pipeline d'extraction de la CIN (carte d'identite nationale tunisienne).
"""

from PIL import Image

from app.ocr.inference import query_qwen
from app.ocr.image_processing import crop_card_region
from app.ocr.prompts.cin_prompts import PROMPT_CIN


def run_extraction_flow_cin(image: Image.Image) -> tuple:
    image_cropped = crop_card_region(image)
    parsed, raw, _ = query_qwen(
        image_cropped, PROMPT_CIN, max_tokens=150,
        with_preprocessing=True, resolution_limit=512, label="CIN"
    )
    return (parsed if parsed else {}), raw