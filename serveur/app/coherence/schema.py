#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/coherence/schema.py

Chaque type de document (constat, CIN, facture, carte grise, permis) a sa
propre structure JSON issue de son pipeline OCR respectif. Ce module fait
la traduction : il extrait, pour un dossier complet, les valeurs
"normalisees" dont le moteur de coherence a besoin (identite, dates,
montants, dommages), independamment de la forme exacte du JSON source.

Entree attendue pour build_normalized_dossier() : un dict
{
  "constat": <extracted_data du router_pipeline pour un constat>,
  "cin": <...>,
  "facture": <...>,
  "carte_grise": <...> ou None,
  "permis": <...> ou None,
}
"""

import re
from typing import Any, Dict, List, Optional


def _get(d: Optional[Dict], *path, default=None):
    """Acces securise a un chemin imbrique, quel que soit le type de document."""
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key, default)
    return cur if cur is not None else default


def _unwrap_value(field: Any) -> Any:
    """
    Certains pipelines (CIN, facture, carte grise, permis) enveloppent
    chaque champ dans {"value": ...}. D'autres (constat) non. On normalise.
    """
    if isinstance(field, dict) and "value" in field and len(field) == 1:
        val = field["value"]
        return None if val == "Non specifie" else val
    return field


def build_normalized_dossier(documents: Dict[str, Optional[Dict]]) -> Dict[str, Any]:
    """
    Construit une vue normalisee du dossier a partir des extracted_data
    de chaque document disponible. Les documents absents (None) donnent
    des valeurs None dans le resultat -> les regles de coherence doivent
    gerer l'absence de donnee sans planter (voir chaque check_*.py).
    """
    constat = documents.get("constat")
    cin = documents.get("cin")
    facture = documents.get("facture")
    carte_grise = documents.get("carte_grise")
    permis = documents.get("permis")

    normalized = {
        "constat": {
            "date_accident": _get(constat, "1. Date et Lieu", "Date"),
            "lieu_accident": _get(constat, "1. Date et Lieu", "Lieu"),
            "conducteur_a_nom": _get(constat, "7. Identite du Conducteur", "Vehicule A", "Nom"),
            "conducteur_a_prenom": _get(constat, "7. Identite du Conducteur", "Vehicule A", "Prenom"),
            "conducteur_a_permis": _get(constat, "7. Identite du Conducteur", "Vehicule A", "Permis de conduire N"),
            "assure_a_nom": _get(constat, "8. Assure", "Vehicule A", "Nom/Prenom"),
            "immatriculation_a": _get(constat, "9. Identite du Vehicule", "Vehicule A", "N immatriculation"),
            "circonstances_a": _get(constat, "12. Circonstances", "Vehicule A", default=[]),
            "circonstances_b": _get(constat, "12. Circonstances", "Vehicule B", default=[]),
            "confidence_flags": _get(constat, "confidence_flags", default={}),
        },
        "cin": {
            "nom": _unwrap_value(_get(cin, "last_name")),
            "prenom": _unwrap_value(_get(cin, "first_name")),
            "date_naissance": _unwrap_value(_get(cin, "birth_date")),
            "numero_cin": _unwrap_value(_get(cin, "doc_number")),
        } if cin else None,
        "facture": {
            "fournisseur": _unwrap_value(_get(facture, "provider_name")),
            "client": _unwrap_value(_get(facture, "client_name")),
            "date_facture": _unwrap_value(_get(facture, "document_date")),
            "produits": _unwrap_value(_get(facture, "purchased_products")) or [],
            "montant_total": _unwrap_value(_get(facture, "total_amount")),
            "signee": _unwrap_value(_get(facture, "is_signed")),
        } if facture else None,
        "carte_grise": {
            "nom_prenom": _unwrap_value(_get(carte_grise, "nom_prenom")),
            "immatriculation": _unwrap_value(_get(carte_grise, "n_immatriculation")),
            "constructeur": _unwrap_value(_get(carte_grise, "constructeur")),
        } if carte_grise else None,
        "permis": {
            "nom": _unwrap_value(_get(permis, "nom")),
            "prenom": _unwrap_value(_get(permis, "prenom")),
            "numero_permis": _unwrap_value(_get(permis, "numero_permis")),
        } if permis else None,
    }
    return normalized