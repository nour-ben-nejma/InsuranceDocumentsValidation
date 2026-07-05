# -*- coding: utf-8 -*-
"""
app/ocr/prompts/permis_prompts.py

Prompt d'extraction du permis de conduire tunisien.
Champs numerotes 1-13 sur le document (numero de permis, date de
delivrance, nom, prenom, lieu/date de naissance, numero de la carte,
adresse).
"""

PROMPT_PERMIS = """\
Cette image est un permis de conduire tunisien (carte rose/violette,
"REPUBLIQUE TUNISIENNE - PERMIS DE CONDUIRE"). Les champs sont numerotes
1 a 8 sur la carte :
  1. Numero de permis
  2. Date de delivrance
  3. Nom (en MAJUSCULES latines, ligne du haut)
  4. Prenom (en MAJUSCULES latines, ligne juste EN DESSOUS du nom -
     c'est un mot DIFFERENT du nom, jamais le meme)
  5. Lieu de naissance, puis date de naissance juste en dessous
  6. Numero de la carte
  7. Adresse (generalement ecrite en ARABE manuscrit ou imprime -
     recopie EXACTEMENT le texte arabe visible dans ce champ,
     n'invente JAMAIS une adresse en lettres latines a partir
     d'autres champs de la carte)
 

Extrais UNIQUEMENT les valeurs reellement visibles dans CHAQUE champ
numerote correspondant. Ne recopie pas la valeur d'un champ dans un autre.
Si un champ est absent ou illisible, mets null.

Retourne UNIQUEMENT ce JSON, sans texte ni fences markdown :
{
  "numero_permis": null,
  "date_delivrance": null,
  "nom": null,
  "prenom": null,
  "lieu_naissance": null,
  "date_naissance": null,
  "numero_carte": null,
  "adresse": null
}"""