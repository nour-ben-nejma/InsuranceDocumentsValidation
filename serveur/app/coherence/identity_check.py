#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/coherence/identity_check.py

Verifie que l'identite (nom/prenom) declaree dans le constat amiable
correspond a celle de la CIN, et si disponibles, de la carte grise et
du permis de conduire. Aucun LLM : comparaison textuelle normalisee +
similarite de chaines (difflib, stdlib).
"""

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

SIMILARITY_THRESHOLD = 0.72  # en dessous -> consideres comme des noms differents


def _normalize_name(value: Optional[str]) -> str:
    if not value:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _names_match(name1: Optional[str], name2: Optional[str]) -> bool:
    n1, n2 = _normalize_name(name1), _normalize_name(name2)
    if not n1 or not n2:
        return True  # absence de donnee -> pas de contradiction, juste rien a comparer
    return _similarity(n1, n2) >= SIMILARITY_THRESHOLD


def check_identity_coherence(normalized_dossier: Dict[str, Any]) -> List[Dict]:
    """
    Retourne une liste d'anomalies (vide si tout coherent). Chaque anomalie :
    {"rule": ..., "severity": "mineure"|"majeure", "detail": ...}
    """
    anomalies: List[Dict] = []

    constat = normalized_dossier.get("constat") or {}
    cin = normalized_dossier.get("cin")
    permis = normalized_dossier.get("permis")
    carte_grise = normalized_dossier.get("carte_grise")

    conducteur_a_nom_complet = f"{constat.get('conducteur_a_nom') or ''} {constat.get('conducteur_a_prenom') or ''}".strip()
    assure_a = constat.get("assure_a_nom")

    # 1. Coherence conducteur (constat) <-> assure (constat)
    # Deux champs du MEME document : s'ils divergent fortement, ce n'est pas
    # forcement une erreur (le conducteur peut differer de l'assure), donc
    # severite mineure, juste a titre informatif pour l'agent.
    if conducteur_a_nom_complet and assure_a and not _names_match(conducteur_a_nom_complet, assure_a):
        msg = (f"Le conducteur declare ('{conducteur_a_nom_complet}') differe de "
               f"l'assure ('{assure_a}') dans le constat. Peut etre normal "
               f"(conducteur autorise different du proprietaire).")
        anomalies.append({
            "rule": "identite_conducteur_vs_assure",
            "severity": "mineure",
            "message": msg,
            "detail": msg,
        })

    # 2. Coherence constat <-> CIN
    if cin:
        cin_nom_complet = f"{cin.get('nom') or ''} {cin.get('prenom') or ''}".strip()
        if conducteur_a_nom_complet and cin_nom_complet and not _names_match(conducteur_a_nom_complet, cin_nom_complet):
            msg = (f"Le nom du conducteur dans le constat ('{conducteur_a_nom_complet}') "
                   f"ne correspond pas au nom sur la CIN fournie ('{cin_nom_complet}').")
            anomalies.append({
                "rule": "identite_constat_vs_cin",
                "severity": "majeure",
                "message": msg,
                "detail": msg,
            })

    # 3. Coherence constat <-> permis de conduire (si fourni)
    if permis:
        permis_nom_complet = f"{permis.get('nom') or ''} {permis.get('prenom') or ''}".strip()
        if conducteur_a_nom_complet and permis_nom_complet and not _names_match(conducteur_a_nom_complet, permis_nom_complet):
            msg = (f"Le nom du conducteur dans le constat ('{conducteur_a_nom_complet}') "
                   f"ne correspond pas au nom sur le permis de conduire fourni ('{permis_nom_complet}').")
            anomalies.append({
                "rule": "identite_constat_vs_permis",
                "severity": "majeure",
                "message": msg,
                "detail": msg,
            })

        permis_num_constat = constat.get("conducteur_a_permis")
        permis_num_carte = permis.get("numero_permis")
        if permis_num_constat and permis_num_carte:
            n1 = re.sub(r"\D", "", str(permis_num_constat))
            n2 = re.sub(r"\D", "", str(permis_num_carte))
            if n1 and n2 and n1 != n2:
                msg = (f"Le numero de permis dans le constat ('{permis_num_constat}') "
                       f"ne correspond pas au numero sur le permis fourni ('{permis_num_carte}').")
                anomalies.append({
                    "rule": "numero_permis_incoherent",
                    "severity": "majeure",
                    "message": msg,
                    "detail": msg,
                })

    # 4. Coherence immatriculation constat <-> carte grise (si fournie)
    if carte_grise:
        immat_constat = constat.get("immatriculation_a")
        immat_carte_grise = carte_grise.get("immatriculation")
        if immat_constat and immat_carte_grise:
            n1 = re.sub(r"[^A-Za-z0-9]", "", str(immat_constat)).upper()
            n2 = re.sub(r"[^A-Za-z0-9]", "", str(immat_carte_grise)).upper()
            if n1 and n2 and n1 != n2:
                msg = (f"L'immatriculation dans le constat ('{immat_constat}') "
                       f"ne correspond pas a celle de la carte grise ('{immat_carte_grise}').")
                anomalies.append({
                    "rule": "immatriculation_incoherente",
                    "severity": "majeure",
                    "message": msg,
                    "detail": msg,
                })

        nom_carte_grise = carte_grise.get("nom_prenom")
        if assure_a and nom_carte_grise and not _names_match(assure_a, nom_carte_grise):
            msg = (f"Le proprietaire sur la carte grise ('{nom_carte_grise}') differe "
                   f"de l'assure declare dans le constat ('{assure_a}'). "
                   f"Peut etre normal si le vehicule a change de mains ou si "
                   f"le conducteur n'est pas le proprietaire.")
            anomalies.append({
                "rule": "proprietaire_vehicule_incoherent",
                "severity": "mineure",
                "message": msg,
                "detail": msg,
            })

    return anomalies