import os
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.models.dossier_schema import DossierResponse
from app.ocr.pipelines.router_pipeline import extract_text_from_image
from app.core.storage import get_storage_provider

router = APIRouter()


# ─────────────────────────────────────────────────────────
# POST /{dossier_id}/analyse  — OCR complet + cohérence
# ─────────────────────────────────────────────────────────
@router.post("/{dossier_id}/analyse", response_model=DossierResponse)
def analyse_dossier(dossier_id: str, db: Session = Depends(get_db)):
    db_dossier = crud.get_dossier(db, dossier_id)
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    extracted = {}
    docs = db_dossier.docs
    storage = get_storage_provider()

    for doc_key, state in docs.items():
        if state.get("fileName") and not state.get("unavailable"):
            local_path = storage.get_local_filepath(dossier_id, doc_key)
            if local_path and os.path.exists(local_path):
                res = extract_text_from_image(local_path)
                if res.get("status") == "success":
                    extracted[doc_key] = res.get("extracted_data", {})

    from app.coherence.aggregator import aggregate_report
    report = aggregate_report(extracted)
    updated_dossier = crud.update_dossier_report(db, dossier_id, report, status=report["global"])
    return updated_dossier


# ─────────────────────────────────────────────────────────
# PATCH /{dossier_id}/extracted  — Sauvegarde champs modifiés
# ─────────────────────────────────────────────────────────
class ExtractedPatch(BaseModel):
    doc_key: str
    fields: Dict[str, Any]

@router.patch("/{dossier_id}/extracted", response_model=DossierResponse)
def save_extracted(dossier_id: str, body: ExtractedPatch, db: Session = Depends(get_db)):
    """
    Persiste les champs modifiés manuellement par l'utilisateur pour un document donné.
    Les modifications sont stockées dans extracted_overrides (séparément du rapport OCR).
    """
    db_dossier = crud.get_dossier(db, dossier_id)
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    updated = crud.update_extracted_overrides(db, dossier_id, body.doc_key, body.fields)
    return updated


# ─────────────────────────────────────────────────────────
# POST /{dossier_id}/reanalyse  — Cohérence uniquement (sans OCR)
# ─────────────────────────────────────────────────────────
@router.post("/{dossier_id}/reanalyse", response_model=DossierResponse)
def reanalyse_dossier(dossier_id: str, db: Session = Depends(get_db)):
    """
    Relance uniquement la vérification de cohérence sans refaire l'OCR.
    Utilise les données extraites du dernier rapport, fusionnées avec
    les éventuelles modifications manuelles de l'utilisateur (extracted_overrides).
    """
    db_dossier = crud.get_dossier(db, dossier_id)
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    # Récupérer les données extraites du dernier rapport OCR
    last_report = db_dossier.report or {}
    base_extracted: Dict[str, Any] = last_report.get("extracted", {})

    if not base_extracted:
        raise HTTPException(
            status_code=400,
            detail="Aucune donnée extraite disponible. Lancez d'abord une analyse complète."
        )

    # Fusionner avec les overrides manuels (les overrides écrasent l'OCR champ par champ)
    overrides: Dict[str, Any] = db_dossier.extracted_overrides or {}
    merged: Dict[str, Any] = {}
    for doc_key, ocr_fields in base_extracted.items():
        if isinstance(ocr_fields, dict):
            doc_overrides = overrides.get(doc_key, {})
            merged[doc_key] = {**ocr_fields, **doc_overrides}
        else:
            merged[doc_key] = ocr_fields

    # Ajouter les docs qui n'ont que des overrides (pas d'OCR)
    for doc_key, override_fields in overrides.items():
        if doc_key not in merged:
            merged[doc_key] = override_fields

    from app.coherence.aggregator import aggregate_report
    report = aggregate_report(merged)

    # Préserver les données fusionnées telles quelles dans le rapport
    # (évite que la normalisation interne ne perde des champs modifiés manuellement)
    report["extracted"] = {k: v for k, v in merged.items() if v}

    updated_dossier = crud.update_dossier_report(db, dossier_id, report, status=report["global"])
    return updated_dossier
