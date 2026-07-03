# -*- coding: utf-8 -*-
"""
app/ocr/prompts/facture_prompts.py

Prompt d'extraction de la facture de reparation.
"""

PROMPT_FACTURE = (
    "Analyse cette facture. Extrais les donnees reelles visibles.\n"
    "JSON uniquement (pas de fences, pas de texte) :\n"
    '{"provider_name":null,"client_name":null,"document_date":null,'
    ' "purchased_products":null,"total_amount":null,"is_signed":false}\n'
    "Si une valeur est absente, mets null."
)