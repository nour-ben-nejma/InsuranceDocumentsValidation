#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/coherence/date_check.py

Logique de validation des dates :
1. La date de la facture de réparation ne doit pas être antérieure à la date de l'accident.
2. La date de l'accident doit se situer dans la période de validité de l'assurance.
3. Le permis de conduire doit avoir été délivré avant la date de l'accident.
"""

import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def parse_date(date_str: Any) -> Optional[datetime]:
    """Parse a date string with various common formats."""
    if not date_str or not isinstance(date_str, str):
        return None
    
    # Clean the date string
    cleaned = date_str.strip().replace(" ", "")
    # Standardize delimiters
    cleaned = re.sub(r"[-.]", "/", cleaned)
    
    # Try common formats
    formats = [
        "%d/%m/%Y",  # 12/04/2026
        "%Y/%m/%d",  # 2026/04/12
        "%d/%m/%y",  # 12/04/26
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
            
    # Try parsing matching digits
    match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", cleaned)
    if match:
        d, m, y = match.groups()
        if len(y) == 2:
            y = "20" + y
        try:
            return datetime(int(y), int(m), int(d))
        except ValueError:
            pass
            
    return None

def check_dates_coherence(normalized_dossier: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Checks dates coherence and returns list of anomalies.
    """
    anomalies: List[Dict[str, Any]] = []
    
    constat = normalized_dossier.get("constat") or {}
    facture = normalized_dossier.get("facture")
    
    accident_date_str = constat.get("date_accident")
    accident_date = parse_date(accident_date_str)
    
    # If we don't have a valid accident date, we can't compare other dates to it
    if not accident_date:
        if accident_date_str and accident_date_str.lower() != "null":
            logger.warning(f"Impossible de parser la date de l'accident : {accident_date_str}")
        return anomalies

    # 1. Facture Date vs Accident Date
    if facture:
        facture_date_str = facture.get("date_facture")
        facture_date = parse_date(facture_date_str)
        if facture_date:
            if facture_date < accident_date:
                msg = (f"La facture est datée du {facture_date.strftime('%d/%m/%Y')}, "
                       f"ce qui est antérieur à la date de l'accident ({accident_date.strftime('%d/%m/%Y')}).")
                anomalies.append({
                    "rule": "date_facture_anterieure_accident",
                    "severity": "majeure",
                    "message": msg,
                    "detail": msg
                })
        elif facture_date_str and facture_date_str.lower() != "null":
            logger.warning(f"Impossible de parser la date de la facture : {facture_date_str}")

    # 2. Accident Date vs Insurance Validity
    ins_du_str = constat.get("assurance_validite_du")
    ins_au_str = constat.get("assurance_validite_au")
    ins_du = parse_date(ins_du_str)
    ins_au = parse_date(ins_au_str)
    
    if ins_du and ins_au:
        if accident_date < ins_du or accident_date > ins_au:
            msg = (f"L'accident ({accident_date.strftime('%d/%m/%Y')}) s'est produit en dehors "
                   f"de la période de validité de l'assurance (du {ins_du.strftime('%d/%m/%Y')} au {ins_au.strftime('%d/%m/%Y')}).")
            anomalies.append({
                "rule": "assurance_expiree_lors_accident",
                "severity": "majeure",
                "message": msg,
                "detail": msg
            })
    elif ins_du_str or ins_au_str:
        logger.warning(f"Dates d'assurance invalides ou incomplètes : du={ins_du_str}, au={ins_au_str}")

    # 3. Permis Issue Date vs Accident Date
    permis_delivre_str = constat.get("conducteur_a_permis_delivre")
    permis_delivre = parse_date(permis_delivre_str)
    if permis_delivre:
        if permis_delivre > accident_date:
            msg = (f"Le permis de conduire a été délivré le {permis_delivre.strftime('%d/%m/%Y')}, "
                   f"soit après la date de l'accident ({accident_date.strftime('%d/%m/%Y')}).")
            anomalies.append({
                "rule": "permis_delivre_apres_accident",
                "severity": "majeure",
                "message": msg,
                "detail": msg
            })
            
    # 4. Coherence Date Delivrance Permis (Constat vs Permis)
    permis = normalized_dossier.get("permis")
    if permis:
        permis_date_str = permis.get("date_delivrance")
        permis_date = parse_date(permis_date_str)
        if permis_delivre and permis_date:
            if permis_delivre != permis_date:
                msg = (f"La date de delivrance du permis sur le constat ({permis_delivre.strftime('%d/%m/%Y')}) "
                       f"ne correspond pas a la date sur le permis fourni ({permis_date.strftime('%d/%m/%Y')}).")
                anomalies.append({
                    "rule": "date_delivrance_permis_incoherente",
                    "severity": "mineure",
                    "message": msg,
                    "detail": msg
                })
                
    return anomalies
