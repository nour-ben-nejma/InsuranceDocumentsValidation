#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/ocr/pipelines/photos_pipeline.py

Pipeline d'analyse visuelle des photos de véhicules accidentés pour détecter les pièces endommagées.
"""

from PIL import Image
from app.ocr.inference import query_qwen

PROMPT_PHOTOS = """Tu es un expert en estimation de dégâts automobiles.
Regarde attentivement cette photo de véhicule accidenté.
Identifie toutes les pièces/zones qui présentent des dégâts visibles (bosses, rayures, fissures, cassures, enfoncements).
Voici la liste exacte des zones autorisées (tu ne dois utiliser que des noms de cette liste) :
- Pare-chocs avant
- Pare-chocs arrière
- Aile avant gauche
- Aile avant droite
- Aile arrière gauche
- Aile arrière droite
- Portière avant gauche
- Portière avant droite
- Portière arrière gauche
- Portière arrière droite
- Capot
- Optique avant gauche
- Optique avant droit
- Feu arrière gauche
- Feu arrière droit
- Pare-brise
- Lunette arrière
- Rétroviseur gauche
- Rétroviseur droit
- Radiateur / Moteur

Retourne UNIQUEMENT un objet JSON (sans fences markdown, pas de texte d'explication) contenant les pièces endommagées, par exemple :
{"pieces_endommagees": ["Pare-chocs avant", "Optique avant gauche"]}

Si aucun dégât n'est visible sur les pièces listées, retourne :
{"pieces_endommagees": []}"""

def run_extraction_flow_photos(image: Image.Image) -> tuple:
    parsed, raw, _ = query_qwen(
        image, PROMPT_PHOTOS, max_tokens=150, resolution_limit=768, label="photos"
    )
    fields = parsed if parsed else {"pieces_endommagees": []}
    return fields, raw
