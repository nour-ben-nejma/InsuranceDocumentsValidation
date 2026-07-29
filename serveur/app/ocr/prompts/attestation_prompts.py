# -*- coding: utf-8 -*-
"""
app/ocr/prompts/attestation_prompts.py
"""

PROMPT_ATTESTATION = """\
Cette image est une attestation d'assurance automobile tunisienne (logo FTUSA, \
"Fédération Tunisienne des Sociétés d'Assurances", ou nom d'une compagnie comme \
COMAR, STAR, ASTREE, GAT, MAE, LLOYD, TUNIS RE...).

Extrais les informations suivantes en te basant STRICTEMENT sur le texte visible :

1. "compagnie" : Nom de la compagnie d'assurance (champ "شركة التأمين" ou "Pour la compagnie", \
ex: "COMAR ASSURANCES", "STAR", "ASTREE").

2. "nom_prenom" : Nom et Prenom complets de l'assure. \
Champ "Nom et Prénom / Raison Sociale" ou "الاسم واللقب / الاسم الاجتماعي".

3. "date_debut" : Date debut de validite. Champ "Du" / "من", format JJ/MM/AAAA.

4. "date_fin" : Date fin de validite. Champ "Au" / "إلى", format JJ/MM/AAAA.

5. "immatriculation" : Numero d'immatriculation COMPLET du vehicule. \
Champ "N° Immatriculation" ou "رقم الترسيم / العرتنة". \
IMPORTANT : Le format tunisien est compose de 3 parties : un nombre, puis "تونس" ou "TUN", \
puis un autre nombre (ex: "216 تونس 7182" ou "216 TUN 7182"). \
Recopie les 3 parties INTEGRALEMENT dans l'ordre. Ne prends pas seulement la derniere partie.

6. "marque" : Marque du vehicule. Champ "Marque" / "الصانع" (ex: "KIA", "VOLKSWAGEN").

7. "type_commercial" : Type du vehicule. Champ "Type" / "النوع" (ex: "RIO", "GOLF").

Si un champ est absent ou illisible, mets null.

Retourne UNIQUEMENT ce JSON, sans texte ni markdown :
{
  "compagnie": null,
  "nom_prenom": null,
  "date_debut": null,
  "date_fin": null,
  "immatriculation": null,
  "marque": null,
  "type_commercial": null
}"""
