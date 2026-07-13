import os
import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.models.dossier_schema import DocState, DossierResponse
from app.core.storage import get_storage_provider

router = APIRouter()

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

    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    filename = f"{dossier_id}_{doc_key}{ext}"

    content = await file.read()
    
    storage = get_storage_provider()
    storage.upload_file(content, filename)

    state = DocState(
        fileName=file.filename,
        fileSize=len(content),
        uploadedAt=int(time.time() * 1000),
        unavailable=False
    )
    
    # Update state and reset the report/status because the document changed
    crud.update_doc_state(db, dossier_id, doc_key, state)
    crud.update_dossier_report(db, dossier_id, None, status="en_cours")
    
    # Return refreshed dossier
    return crud.get_dossier(db, dossier_id)

@router.post("/{dossier_id}/documents/{doc_key}/unavailable", response_model=DossierResponse)
def mark_document_unavailable(dossier_id: str, doc_key: str, db: Session = Depends(get_db)):
    db_dossier = crud.get_dossier(db, dossier_id)
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    # Delete any existing file in storage
    storage = get_storage_provider()
    storage.delete_file(dossier_id, doc_key)

    state = DocState(
        fileName=None,
        fileSize=None,
        uploadedAt=int(time.time() * 1000),
        unavailable=True
    )
    
    # Update state and reset the report/status because the document changed
    crud.update_doc_state(db, dossier_id, doc_key, state)
    crud.update_dossier_report(db, dossier_id, None, status="en_cours")
    
    return crud.get_dossier(db, dossier_id)

@router.delete("/{dossier_id}/documents/{doc_key}", response_model=DossierResponse)
def delete_document(dossier_id: str, doc_key: str, db: Session = Depends(get_db)):
    """Delete a document file and reset its state."""
    db_dossier = crud.get_dossier(db, dossier_id)
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    storage = get_storage_provider()
    storage.delete_file(dossier_id, doc_key)

    # Reset state and report/status
    crud.delete_document(db, dossier_id, doc_key)
    crud.update_dossier_report(db, dossier_id, None, status="en_cours")
    
    return crud.get_dossier(db, dossier_id)

@router.get("/{dossier_id}/documents/{doc_key}/view")
def view_document(dossier_id: str, doc_key: str, db: Session = Depends(get_db)):
    """Serve the uploaded file for viewing."""
    db_dossier = crud.get_dossier(db, dossier_id)
    if not db_dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    storage = get_storage_provider()
    url = storage.get_view_url(dossier_id, doc_key)
    if not url:
        raise HTTPException(status_code=404, detail="File not found in storage")

    if url.startswith("http://") or url.startswith("https://"):
        return RedirectResponse(url)

    # Local fallback
    local_path = storage.get_local_filepath(dossier_id, doc_key)
    if not local_path or not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(local_path)
