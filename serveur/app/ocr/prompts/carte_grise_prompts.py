# -*- coding: utf-8 -*-
"""
app/ocr/prompts/carte_grise_prompts.py

Prompt d'extraction du certificat d'immatriculation tunisien (carte grise).
Champs presents sur le document : identite du proprietaire, adresse, CIN,
numero d'immatriculation, constructeur/type/modele, date de mise en
circulation (DPMC).
"""

PROMPT_CARTE_GRISE = """\
Cette image est un certificat d'immatriculation tunisien (carte grise).
Extrais UNIQUEMENT les valeurs imprimees/manuscrites reellement visibles.
Conserve le texte arabe intact, ne le traduis pas.
Le numero d'immatriculation est compose de 3 parties visibles sur la carte
(ex: registre a gauche + lettre serie + numero) : reconstitue-le au format
tel qu'il apparait sur les plaques tunisiennes (ex: "216 TUN 7182").
Si un champ est absent ou illisible, mets null.

Retourne UNIQUEMENT ce JSON, sans texte ni fences markdown :
{
  "nom_prenom": null,
  "adresse": null,
  "cin_ou_mf": null,
  "activite": null,
  "genre": null,
  "n_immatriculation": null,
  "n_serie_type": null,
  "constructeur": null,
  "type_commercial": null,
  "type_constructeur": null,
  "date_mise_circulation": null
}"""