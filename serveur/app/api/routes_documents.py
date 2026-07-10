import os
import glob
import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.models.dossier_schema import DocState, DossierResponse

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "images")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/{dossier_id}/documents/{doc_key}", response_model=DossierResponse)
async def upload_document(
    dossier_id: str, 
    doc_key: str, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    db_dossier = crud.get_dossier(db, dossier_id)
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    # Remove old file for this doc_key first
    for old_file in glob.glob(os.path.join(UPLOAD_DIR, f"{dossier_id}_{doc_key}.*")):
        os.remove(old_file)

    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    filename = f"{dossier_id}_{doc_key}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    state = DocState(
        fileName=file.filename,
        fileSize=len(content),
        uploadedAt=int(time.time() * 1000),
        unavailable=False
    )
    
    updated_dossier = crud.update_doc_state(db, dossier_id, doc_key, state)
    return updated_dossier

@router.post("/{dossier_id}/documents/{doc_key}/unavailable", response_model=DossierResponse)
def mark_document_unavailable(dossier_id: str, doc_key: str, db: Session = Depends(get_db)):
    db_dossier = crud.get_dossier(db, dossier_id)
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    state = DocState(
        fileName=None,
        fileSize=None,
        uploadedAt=int(time.time() * 1000),
        unavailable=True
    )
    
    updated_dossier = crud.update_doc_state(db, dossier_id, doc_key, state)
    return updated_dossier

@router.delete("/{dossier_id}/documents/{doc_key}", response_model=DossierResponse)
def delete_document(dossier_id: str, doc_key: str, db: Session = Depends(get_db)):
    """Delete a document file and reset its state."""
    db_dossier = crud.get_dossier(db, dossier_id)
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    # Delete the physical file from disk
    for old_file in glob.glob(os.path.join(UPLOAD_DIR, f"{dossier_id}_{doc_key}.*")):
        os.remove(old_file)

    updated_dossier = crud.delete_document(db, dossier_id, doc_key)
    return updated_dossier

@router.get("/{dossier_id}/documents/{doc_key}/view")
def view_document(dossier_id: str, doc_key: str, db: Session = Depends(get_db)):
    """Serve the uploaded file for viewing."""
    db_dossier = crud.get_dossier(db, dossier_id)
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    matches = glob.glob(os.path.join(UPLOAD_DIR, f"{dossier_id}_{doc_key}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="File not found on disk")

    file_path = matches[0]
    return FileResponse(file_path)
