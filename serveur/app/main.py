#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/main.py

Point d'entree du serveur FastAPI.

Responsabilites :
  1. Au demarrage (lifespan) : charger le modele Qwen2.5-VL UNE SEULE FOIS
     via ModelManager, puis lancer le warmup GPU.
  2. Monter les routers de l'API (dossiers, documents, analyse).
  3. Exposer un endpoint /health pour verifier que le serveur + le modele
     sont prets, utile pour tester rapidement sans passer par le frontend.

Lancement (depuis serveur/, venv_ocr active) :
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Remarque sur --reload : pratique en dev, mais chaque reload redemarre le
process Python -> le modele est recharge (10-40s). Desactive --reload
des que tu testes des inferences repetees pour ne pas perdre de temps.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.model_loader import ModelManager
from app.core.warmup import warmup_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------- STARTUP ----------
    print("=" * 60)
    print("[STARTUP] Demarrage du serveur InsuranceDocumentValidation")
    print("=" * 60)

    t0 = time.perf_counter()
    mgr = ModelManager.get_instance()
    mgr.load()
    warmup_model()
    print(f"[STARTUP] Serveur pret en {time.perf_counter() - t0:.1f}s au total")

    yield  # <-- le serveur tourne ici

    # ---------- SHUTDOWN ----------
    print("[SHUTDOWN] Arret du serveur, liberation de la VRAM...")
    mgr.unload()


app = FastAPI(
    title="InsuranceDocumentValidation API",
    description="Extraction OCR/Vision + verification de coherence "
                 "(constat amiable, CIN, facture) pour l'agent d'assurance.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS : a restreindre en production a l'origine reelle du frontend agent.
# En dev, on autorise localhost sur les ports usuels (Vite/React/Vue).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """
    Verifie que le serveur tourne ET que le modele est bien charge.
    A appeler en premier pour diagnostiquer un probleme avant de tester
    un vrai upload de document.
    """
    mgr = ModelManager.get_instance()
    return {
        "status": "ok" if mgr.is_loaded else "model_not_loaded",
        "model_loaded": mgr.is_loaded,
        "device": mgr.device,
    }


# ---------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------
# Decommente au fur et a mesure que chaque fichier de route est rempli.
# Les imports sont groupes ici pour que main.py reste le seul endroit
# a connaitre l'ensemble des routes exposees par l'API.

# from app.api.routes_dossiers import router as dossiers_router
# from app.api.routes_documents import router as documents_router
# from app.api.routes_analyse import router as analyse_router
#
# app.include_router(dossiers_router, prefix="/dossiers", tags=["Dossiers"])
# app.include_router(documents_router, prefix="/dossiers", tags=["Documents"])
# app.include_router(analyse_router, prefix="/dossiers", tags=["Analyse"])


if __name__ == "__main__":
    # Lancement direct pour debug : python app/main.py
    # (prefer uvicorn app.main:app --reload en usage normal)
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)