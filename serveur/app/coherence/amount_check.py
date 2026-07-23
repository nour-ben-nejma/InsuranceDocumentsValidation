#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/coherence/amount_check.py

Vérifie la cohérence du client facturé et du montant de la facture.
"""

import logging
from typing import Any, Dict, List
from app.coherence.identity_check import _names_match

logger = logging.getLogger(__name__)

def check_amounts_coherence(normalized_dossier: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Checks amount and client name coherence and returns list of anomalies.
    """
    anomalies: List[Dict[str, Any]] = []
    
    constat = normalized_dossier.get("constat") or {}
    facture = normalized_dossier.get("facture")
    
    if not facture:
        return anomalies
        
    # 1. client_name vs driver/assured
    client_facture = facture.get("client")
    conducteur_nom_complet = f"{constat.get('conducteur_a_nom') or ''} {constat.get('conducteur_a_prenom') or ''}".strip()
    assure_nom = constat.get("assure_a_nom")
    
    if client_facture and (conducteur_nom_complet or assure_nom):
        match_conducteur = _names_match(client_facture, conducteur_nom_complet) if conducteur_nom_complet else False
        match_assure = _names_match(client_facture, assure_nom) if assure_nom else False
        
        if not match_conducteur and not match_assure:
            msg = (f"Le client facturé ('{client_facture}') ne correspond "
                   f"ni au conducteur ('{conducteur_nom_complet or 'Non spécifié'}') "
                   f"ni à l'assuré ('{assure_nom or 'Non spécifié'}') indiqués sur le constat.")
            anomalies.append({
                "rule": "client_facture_incoherent",
                "severity": "mineure",
                "message": msg,
                "detail": msg
            })

    # 2. Total amount positive check
    try:
        raw_amount = facture.get("montant_total")
        if raw_amount is not None:
            # Clean and parse float
            import re
            cleaned_amount = re.sub(r"[^\d.,]", "", str(raw_amount)).replace(",", ".")
            amount = float(cleaned_amount) if cleaned_amount else 0.0
            
            if amount <= 0.0:
                msg = "Le montant total de la facture est nul ou invalide."
                anomalies.append({
                    "rule": "montant_facture_invalide",
                    "severity": "mineure",
                    "message": msg,
                    "detail": msg
                })
    except (ValueError, TypeError):
        msg = "Le montant total de la facture n'a pas pu être lu correctement."
        anomalies.append({
            "rule": "montant_facture_illisible",
            "severity": "mineure",
            "message": msg,
            "detail": msg
        })
        
    return anomalies
