#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/ocr/confidence.py

Compare deux extractions JSON du meme document (deux appels VLM sur le
meme crop) et identifie les champs sur lesquels le modele s'est contredit.

Principe : le modele 4-bit quantifie n'est pas parfaitement deterministe,
surtout sur du texte manuscrit fin ou des plaques d'immatriculation.
Plutot que de faire confiance aveuglement a un seul appel, on interroge
deux fois et on ne fait confiance qu'aux champs stables entre les deux.
Les champs instables sont remontes a l'agent pour verification manuelle
(coherent avec son role defini dans le cahier des charges).
"""

import re
from typing import Any, Dict, List, Tuple, Optional


def _normalize_for_compare(value: Any) -> Optional[str]:
    """Normalise une valeur avant comparaison : espaces, casse, ponctuation legere."""
    if value is None:
        return None
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    # Tolere les variations mineures de ponctuation autour des slashs/tirets
    text = re.sub(r"\s*([/\-])\s*", r"\1", text)
    return text or None


def diff_paths(d1: Any, d2: Any, prefix: str = "") -> List[str]:
    """
    Parcourt recursivement deux structures JSON de meme forme et retourne
    la liste des chemins ("Section > Sous-champ") ou les valeurs different
    apres normalisation.
    """
    diffs: List[str] = []

    if isinstance(d1, dict) or isinstance(d2, dict):
        d1 = d1 if isinstance(d1, dict) else {}
        d2 = d2 if isinstance(d2, dict) else {}
        for key in set(d1.keys()) | set(d2.keys()):
            child_prefix = f"{prefix}{key} > " if prefix else f"{key} > "
            diffs.extend(diff_paths(d1.get(key), d2.get(key), child_prefix))
    else:
        if _normalize_for_compare(d1) != _normalize_for_compare(d2):
            clean_path = prefix.rstrip(" >") if prefix else "(racine)"
            diffs.append(clean_path)

    return diffs


def merge_double_extraction(
    parsed_1: Optional[Dict],
    parsed_2: Optional[Dict],
    label: str = "",
) -> Tuple[Dict, List[str]]:
    """
    Combine deux extractions du meme document.

    Retourne (resultat_final, champs_en_desaccord).

    Strategie de choix quand il y a desaccord : on garde la 1ere extraction
    (aucune raison objective de preferer l'une a l'autre), mais le champ
    est liste dans champs_en_desaccord pour que l'agent le voie et verifie
    manuellement contre l'image originale.
    """
    if parsed_1 is None and parsed_2 is None:
        print(f"  [CONFIDENCE {label}] Les deux extractions ont echoue.")
        return {}, ["extraction_totalement_echouee"]

    if parsed_1 is None:
        print(f"  [CONFIDENCE {label}] 1ere extraction vide, on garde la 2eme sans comparaison.")
        return parsed_2, ["extraction_1_echouee_fallback_sur_2"]

    if parsed_2 is None:
        print(f"  [CONFIDENCE {label}] 2eme extraction vide, on garde la 1ere sans comparaison.")
        return parsed_1, ["extraction_2_echouee_fallback_sur_1"]

    diffs = diff_paths(parsed_1, parsed_2)

    if diffs:
        print(f"  [CONFIDENCE {label}] {len(diffs)} champ(s) en desaccord entre les 2 passes :")
        for d in diffs:
            print(f"      - {d}")
    else:
        print(f"  [CONFIDENCE {label}] OK Les 2 extractions concordent parfaitement.")

    return parsed_1, diffs