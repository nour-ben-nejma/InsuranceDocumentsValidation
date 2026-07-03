#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/ocr/pipelines/router_pipeline.py

Point d'entree unique du pipeline OCR : classifie le document
(constat_amiable / piece_identite / facture_reparation) puis
dispatch vers le pipeline specialise correspondant.

C'est CETTE fonction (extract_text_from_image) que les routes FastAPI
(app/api/routes_analyse.py) doivent appeler.
"""

import re
import time
import traceback

from PIL import Image
from qwen_vl_utils import process_vision_info
import torch

from app.core.model_loader import get_model_and_processor
from app.ocr.pipelines.constat_pipeline import run_extraction_flow_constat_complete
from app.ocr.pipelines.cin_pipeline import run_extraction_flow_cin
from app.ocr.pipelines.facture_pipeline import run_extraction_flow_facture

_SCHEMA = {
    "facture_reparation": ["provider_name", "client_name", "document_date", "purchased_products", "total_amount"],
    "constat_amiable": ["accident_date", "location", "insurance_company_a", "conductor_a", "assured_a", "vehicle_a"],
    "piece_identite": ["last_name", "first_name", "birth_date", "doc_number"],
}


def _normalize_amount(val) -> float:
    try:
        return float(re.sub(r"[^\d.,]", "", str(val)).replace(" ", "").replace(",", "."))
    except (ValueError, TypeError):
        return 0.0


def _classify_document(image: Image.Image) -> str:
    """Demande au VLM de classifier le type de document en un mot."""
    model, processor = get_model_and_processor()

    classif_prompt = "Quel type de document parmi : facture_reparation, constat_amiable, piece_identite ? Un seul mot."
    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": image, "min_pixels": 256 * 256, "max_pixels": 512 * 512},
            {"type": "text", "text": classif_prompt},
        ]
    }]
    tpl = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    img_in, _ = process_vision_info(messages)
    inputs = processor(text=[tpl], images=img_in, padding=True, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    t0 = time.perf_counter()
    with torch.inference_mode():
        gen_ids = model.generate(**inputs, max_new_tokens=10, do_sample=False)
    doc_type_raw = processor.batch_decode(
        [gen_ids[0][len(inputs["input_ids"][0]):]], skip_special_tokens=True
    )[0].strip()
    print(f"  [TIMING] classification: {time.perf_counter() - t0:.2f}s")
    print(f"  [DEBUG] Classification raw output: '{doc_type_raw}'")

    del inputs, gen_ids
    torch.cuda.empty_cache()

    matched_type = "facture_reparation"
    for t in _SCHEMA:
        if t in doc_type_raw.lower():
            matched_type = t
            break
    print(f"[DEBUG] Classification : '{doc_type_raw}' -> '{matched_type}'")
    return matched_type


def extract_text_from_image(image_path: str) -> dict:
    """
    Point d'entree principal. Prend un chemin d'image local (le fichier
    uploade est d'abord ecrit dans storage/uploads/ par l'API), classifie
    le document, puis extrait ses champs.
    """
    t_total = time.perf_counter()
    try:
        image = Image.open(image_path).convert("RGB")
        matched_type = _classify_document(image)

        if matched_type == "constat_amiable":
            extracted_json, raw_backup, timings = run_extraction_flow_constat_complete(image)
            return {
                "document_type": matched_type,
                "extracted_data": extracted_json,
                "raw_text_backup": raw_backup,
                "latency": timings,
                "total_elapsed_s": round(time.perf_counter() - t_total, 2),
                "status": "success",
            }

        elif matched_type == "piece_identite":
            extracted_fields, raw_backup = run_extraction_flow_cin(image)
            structured = {f: {"value": extracted_fields.get(f) or "Non specifie"}
                          for f in _SCHEMA[matched_type]}
            return {
                "document_type": matched_type,
                "extracted_data": structured,
                "raw_text_backup": raw_backup,
                "total_elapsed_s": round(time.perf_counter() - t_total, 2),
                "status": "success",
            }

        else:
            extracted_fields, raw_backup = run_extraction_flow_facture(image)
            structured = {}
            for f in _SCHEMA[matched_type]:
                val = extracted_fields.get(f)
                if f == "total_amount" and val:
                    val = _normalize_amount(val)
                structured[f] = {"value": val or "Non specifie"}
            structured["is_signed"] = {"value": bool(extracted_fields.get("is_signed", False))}
            return {
                "document_type": matched_type,
                "extracted_data": structured,
                "raw_text_backup": raw_backup,
                "total_elapsed_s": round(time.perf_counter() - t_total, 2),
                "status": "success",
            }

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "error_message": str(e),
                "total_elapsed_s": round(time.perf_counter() - t_total, 2)}