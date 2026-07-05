#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/test_pipeline.py

Teste le pipeline OCR complet (classification + extraction) sur des images
locales, SANS passer par l'API FastAPI. A lancer en premier pour valider
que la migration Colab -> local fonctionne, avant de construire le moteur
de coherence et les routes API par-dessus.

Usage (depuis serveur/, venv_ocr active) :
    python scripts/test_pipeline.py

Place tes images de test dans tests/fixtures/ avant de lancer :
    tests/fixtures/constat_exemple.jpg
    tests/fixtures/cin_exemple.jpg
    tests/fixtures/facture_exemple.jpg
(renomme selon tes vrais fichiers, ou modifie TEST_IMAGES ci-dessous)
"""

import sys
import json
import time
from pathlib import Path

# Permet de lancer "python scripts/test_pipeline.py" depuis serveur/
# sans probleme d'import relatif.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.model_loader import ModelManager
from app.core.warmup import warmup_model
from app.ocr.pipelines.router_pipeline import extract_text_from_image

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

TEST_IMAGES = [
    FIXTURES_DIR / "assurance_constat_page-0001.jpg",
    FIXTURES_DIR / "cin20_jpg (1).jpg",
    FIXTURES_DIR / "20250109_110059.jpg",
    Path("C:/Users/benne/Desktop/InsuranceDocumentsValidation/serveur/tests/fixtures/Capture d'écran 2026-07-05 143813.png"),
    FIXTURES_DIR / "images.jpg",
]


def main():
    print("=" * 60)
    print("TEST DU PIPELINE OCR - InsuranceDocumentValidation")
    print("=" * 60)

    # 1. Chargement du modele (une seule fois, comme dans main.py)
    print("\n[1/3] Chargement du modele...")
    t0 = time.perf_counter()
    mgr = ModelManager.get_instance()
    mgr.load()
    print(f"      OK charge en {time.perf_counter() - t0:.1f}s")

    print("\n[2/3] Warmup GPU...")
    t0 = time.perf_counter()
    warmup_model()
    print(f"      OK warmup en {time.perf_counter() - t0:.1f}s")

    # 2. Verification des fixtures
    missing = [p for p in TEST_IMAGES if not p.exists()]
    if missing:
        print("\n[ATTENTION] Fichiers de test manquants :")
        for p in missing:
            print(f"   - {p}")
        print(f"\nPlace des images dans {FIXTURES_DIR} et adapte TEST_IMAGES "
              f"en haut de ce script si les noms sont differents.")

    existing = [p for p in TEST_IMAGES if p.exists()]
    if not existing:
        print("\nAucune image de test trouvee. Arret.")
        return

    # 3. Extraction sur chaque image
    print(f"\n[3/3] Extraction sur {len(existing)} image(s)...\n")
    results = []
    for img_path in existing:
        print("-" * 60)
        print(f"Fichier : {img_path.name}")
        t0 = time.perf_counter()
        result = extract_text_from_image(str(img_path))
        elapsed = time.perf_counter() - t0

        print(f"Type detecte : {result.get('document_type', 'N/A')}")
        print(f"Statut       : {result.get('status')}")
        print(f"Latence      : {elapsed:.1f}s (rapportee par le pipeline : "
              f"{result.get('total_elapsed_s', '?')}s)")

        if result.get("status") == "error":
            print(f"Erreur : {result.get('error_message')}")
        else:
            print("Champs extraits :")
            print(json.dumps(result.get("extracted_data", {}), ensure_ascii=False, indent=2))

        results.append({"file": img_path.name, "elapsed_s": round(elapsed, 2),
                         "status": result.get("status"),
                         "document_type": result.get("document_type")})
        print()

    # 4. Recapitulatif
    print("=" * 60)
    print("RECAPITULATIF")
    print("=" * 60)
    for r in results:
        print(f"  {r['file']:<30} {r['status']:<10} {r['document_type'] or '?':<20} {r['elapsed_s']}s")

    avg = sum(r["elapsed_s"] for r in results) / len(results)
    print(f"\nLatence moyenne : {avg:.1f}s/document")
    print("Cible cahier des charges : <= 25s/document")
    print("OK" if avg <= 25 else "AU-DESSUS DE LA CIBLE - a optimiser")


if __name__ == "__main__":
    main()