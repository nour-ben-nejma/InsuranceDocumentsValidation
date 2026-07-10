import os
import glob
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db import crud
from app.models.dossier_schema import DossierCreate, DossierResponse

router = APIRouter()

@router.post("", response_model=DossierResponse)
@router.post("/", response_model=DossierResponse)
def create_dossier(dossier: DossierCreate, db: Session = Depends(get_db)):
    return crud.create_dossier(db, dossier)

@router.get("", response_model=List[DossierResponse])
@router.get("/", response_model=List[DossierResponse])
def get_dossiers(db: Session = Depends(get_db)):
    return crud.get_dossiers(db)

@router.get("/{dossier_id}", response_model=DossierResponse)
def get_dossier(dossier_id: str, db: Session = Depends(get_db)):
    db_dossier = crud.get_dossier(db, dossier_id)
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")
    return db_dossier

@router.delete("/{dossier_id}")
def delete_dossier(dossier_id: str, db: Session = Depends(get_db)):
    """Permanently delete a dossier and all its data."""
    # Delete physical files from disk first
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "images")
    if os.path.exists(upload_dir):
        for dossier_file in glob.glob(os.path.join(upload_dir, f"{dossier_id}_*")):
            try:
                os.remove(dossier_file)
            except Exception:
                pass

    success = crud.delete_dossier(db, dossier_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dossier not found")
    return JSONResponse(content={"ok": True})

