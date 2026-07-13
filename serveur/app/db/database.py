import os
from sqlalchemy import create_engine, Column, String, Integer, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage")
os.makedirs(DB_DIR, exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'dossiers.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class DossierDB(Base):
    __tablename__ = "dossiers"

    id = Column(String, primary_key=True, index=True)
    numero = Column(String, index=True)
    client = Column(String)
    createdAt = Column(Integer)
    status = Column(String, default="brouillon")
    docs = Column(JSON, default=dict)
    report = Column(JSON, nullable=True)
    extracted_overrides = Column(JSON, nullable=True)  # Champs modifiés manuellement par l'utilisateur

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
