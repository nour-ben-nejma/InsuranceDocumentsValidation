# -*- coding: utf-8 -*-
"""
app/ocr/prompts/constat_prompts.py

Prompts utilises pour l'extraction du constat amiable (header, vehicule A/B, signature).
"""

# FIX #4 : prompt header en francais
PROMPT_HEADER = """\
Image : en-tete d'un constat amiable tunisien.
Regarde uniquement les cases "1. date de l'accident" et "2. lieu".
Si la case est VIDE (aucune ecriture manuscrite a l interieur), tu DOIS repondre null.
N'invente JAMAIS une date ou un lieu qui n'est pas explicitement ecrit a la main dans la case.
Retourne UNIQUEMENT ce JSON valide, rien d'autre :
{"Date": "JJ/MM/AAAA ou null", "Lieu": "ville/adresse ou null"}"""

PROMPT_SIGNATURE = """\
Cette image contient-elle une signature manuscrite ?
Reponds UNIQUEMENT : {"signed": true} ou {"signed": false}"""


# FIX #1 : prompt cote-aware -> injecte "VEHICULE {side}" pour ancrer le VLM
# FIX #2 : null au lieu de "" -> evite que le VLM copie les labels du formulaire
# FIX #3 : instruction explicite "NE PAS copier les etiquettes imprimes du formulaire"
def make_prompt_vehicule(side: str) -> str:
    return f"""\
Tu analyses la colonne VEHICULE {side} du constat amiable tunisien.
Extrais UNIQUEMENT les valeurs manuscrites (ecrites a la main).
NE PAS copier les etiquettes imprimes du formulaire (ex: "Societe d'Assurances", "Assure", etc.).
Conserve le texte arabe intact. Si un champ est vide, mets null.
Retourne ce JSON (sans fences markdown) :
{{
  "6. Societe d Assurances": {{
    "Assureur": null,
    "Police d Assurance N": null,
    "Agence": null,
    "Validite": {{"du": null, "au": null}}
  }},
  "7. Identite du Conducteur": {{
    "Nom": null,
    "Prenom": null,
    "Adresse": null,
    "Permis de conduire N": null,
    "Delivre le": null
  }},
  "8. Assure": {{
    "Nom/Prenom": null,
    "Adresse": null,
    "Tel": null
  }},
  "9. Identite du Vehicule": {{
    "Marque/Type": null,
    "N immatriculation": null,
    "Sens suivi": {{"Venant de": null, "Allant a": null}}
  }},
  "10. Point de choc initial": null,
  "11. Degats apparents": null
}}"""