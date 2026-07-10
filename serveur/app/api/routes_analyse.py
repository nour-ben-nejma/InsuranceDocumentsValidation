import os
import glob
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.models.dossier_schema import DossierResponse
from app.ocr.pipelines.router_pipeline import extract_text_from_image

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "images")

@router.post("/{dossier_id}/analyse", response_model=DossierResponse)
def analyse_dossier(dossier_id: str, db: Session = Depends(get_db)):
    db_dossier = crud.get_dossier(db, dossier_id)
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    # Run extraction
    extracted = {}
    docs = db_dossier.docs
    for doc_key, state in docs.items():
        if state.get("fileName") and not state.get("unavailable"):
            # Find the file in storage
            pattern = os.path.join(UPLOAD_DIR, f"{dossier_id}_{doc_key}.*")
            matches = glob.glob(pattern)
            if matches:
                file_path = matches[0]
                res = extract_text_from_image(file_path)
                if res.get("status") == "success":
                    data = res.get("extracted_data", {})
                    extracted[doc_key] = data
    
    # Construct a report compatible with frontend
    # Build report using coherence aggregator
    from app.coherence.aggregator import aggregate_report
    report = aggregate_report(extracted)
    
    updated_dossier = crud.update_dossier_report(db, dossier_id, report, status=report["global"])
    return updated_dossier
