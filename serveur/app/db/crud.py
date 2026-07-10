import time
import uuid
from sqlalchemy.orm import Session
from app.db.database import DossierDB
from app.models.dossier_schema import DossierCreate, DocState

def create_dossier(db: Session, dossier: DossierCreate):
    dossier_id = str(uuid.uuid4())
    empty_docs = {
        "carte_grise": {},
        "cin": {},
        "attestation": {},
        "constat": {},
        "facture": {}
    }
    db_dossier = DossierDB(
        id=dossier_id,
        numero=dossier.numero,
        client=dossier.client,
        createdAt=int(time.time() * 1000),
        status="brouillon",
        docs=empty_docs,
        report=None
    )
    db.add(db_dossier)
    db.commit()
    db.refresh(db_dossier)
    return db_dossier

def get_dossiers(db: Session):
    return db.query(DossierDB).order_by(DossierDB.createdAt.desc()).all()

def get_dossier(db: Session, dossier_id: str):
    return db.query(DossierDB).filter(DossierDB.id == dossier_id).first()

def update_doc_state(db: Session, dossier_id: str, doc_key: str, state: DocState):
    db_dossier = get_dossier(db, dossier_id)
    if db_dossier:
        # copy dict to trigger sqlalchemy json update
        docs = dict(db_dossier.docs)
        docs[doc_key] = state.model_dump(exclude_unset=True)
        db_dossier.docs = docs
        db.commit()
        db.refresh(db_dossier)
    return db_dossier

def update_dossier_report(db: Session, dossier_id: str, report: dict, status: str):
    db_dossier = get_dossier(db, dossier_id)
    if db_dossier:
        db_dossier.report = report
        db_dossier.status = status
        db.commit()
        db.refresh(db_dossier)
    return db_dossier

def delete_document(db: Session, dossier_id: str, doc_key: str):
    """Reset a document back to empty state (remove file info)."""
    db_dossier = get_dossier(db, dossier_id)
    if db_dossier:
        docs = dict(db_dossier.docs)
        docs[doc_key] = {}
        db_dossier.docs = docs
        # Reset status to en_cours if it was coherent/a_verifier
        if db_dossier.status in ("coherent", "a_verifier"):
            db_dossier.status = "en_cours"
        db.commit()
        db.refresh(db_dossier)
    return db_dossier

def delete_dossier(db: Session, dossier_id: str):
    """Permanently delete a dossier."""
    db_dossier = get_dossier(db, dossier_id)
    if db_dossier:
        db.delete(db_dossier)
        db.commit()
        return True
    return False
