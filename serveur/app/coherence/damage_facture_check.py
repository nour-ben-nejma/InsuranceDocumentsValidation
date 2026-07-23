#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/coherence/damage_facture_check.py

Vérifie la cohérence à 3 voies entre :
1. Les dégâts déclarés (constat)
2. Les dégâts visibles (photos)
3. Les réparations facturées (facture)
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional

# Liste des zones du véhicule avec leurs mots-clés associés pour le texte
VEHICLE_ZONES = {
    "Pare-chocs avant": ["pare-choc avant", "pare choc avant", "pare-chocs avant", "pc avant", "bouclier avant", "absorbeur avant"],
    "Pare-chocs arrière": ["pare-choc arriere", "pare choc arriere", "pare-chocs arriere", "pc arriere", "bouclier arriere"],
    "Aile avant gauche": ["aile avant gauche", "aile avg"],
    "Aile avant droite": ["aile avant droite", "aile avd"],
    "Aile arrière gauche": ["aile arriere gauche", "aile arg"],
    "Aile arrière droite": ["aile arriere droite", "aile ard"],
    "Portière avant gauche": ["portiere avant gauche", "porte avant gauche", "porte avg", "portiere avg"],
    "Portière avant droite": ["portiere avant droite", "porte avant droite", "porte avd", "portiere avd"],
    "Portière arrière gauche": ["portiere arriere gauche", "porte arriere gauche", "porte arg", "portiere arg"],
    "Portière arrière droite": ["portiere arriere droite", "porte arriere droite", "porte ard", "portiere ard"],
    "Capot": ["capot avant", "capot"],
    "Optique avant gauche": ["optique avant gauche", "phare avant gauche", "feu avant gauche", "phare avg", "feu avg", "projecteur gauche"],
    "Optique avant droit": ["optique avant droit", "phare avant droit", "feu avant droit", "phare avd", "feu avd", "projecteur droit"],
    "Feu arrière gauche": ["feu arriere gauche", "lanterne arriere gauche", "feu arg", "optique arriere gauche"],
    "Feu arrière droit": ["feu arriere droit", "lanterne arriere droit", "feu ard", "optique arriere droit"],
    "Pare-brise": ["pare-brise", "pare brise", "vitre avant", "vitre av"],
    "Lunette arrière": ["lunette arriere", "vitre arriere", "vitre ar"],
    "Rétroviseur gauche": ["retro gauche", "retroviseur gauche", "retro avg", "retroviseur avg"],
    "Rétroviseur droit": ["retro droit", "retroviseur droit", "retro avd", "retroviseur avd"],
    "Radiateur / Moteur": ["radiateur", "moteur", "condenseur", "traverse", "ventilateur", "mecanique"]
}

def _normalize_text(text: Any) -> str:
    if not text:
        return ""
    text = str(text).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\w\s/.-]", "", text)
    return text

def _extract_price(product_str: str) -> float:
    """Tente d'extraire un prix de la ligne de facturation."""
    normalized = product_str.replace(" ", "").replace("TND", "").replace("DT", "").replace("tnd", "").replace("dt", "")
    matches = re.findall(r"(\d+[\d.,]*)", normalized)
    if not matches:
        return 0.0
    
    last_match = matches[-1]
    try:
        last_match = last_match.replace(",", ".")
        if last_match.count(".") > 1:
            parts = last_match.split(".")
            if len(parts[-1]) == 3:
                last_match = "".join(parts[:-1]) + "." + parts[-1]
            else:
                last_match = last_match.replace(".", "")
        return float(last_match)
    except ValueError:
        return 0.0

def build_damage_mapping(normalized_dossier: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Construit la liste des zones avec l'état déclaré, visible, facturé pour l'interface.
    """
    mapping: List[Dict[str, Any]] = []
    
    constat = normalized_dossier.get("constat") or {}
    facture = normalized_dossier.get("facture") or {}
    photos_degats = normalized_dossier.get("photos_degats")
    
    degats_constat = _normalize_text(constat.get("degats_apparents_a"))
    choc_constat = _normalize_text(constat.get("choc_initial_a"))
    
    produits_facture = facture.get("produits") or []
    normalized_produits = []
    for p in produits_facture:
        if isinstance(p, dict):
            p_name = p.get("product_name") or ""
            p_price = p.get("total_price")
            if p_price is None:
                p_price = p.get("unit_price")
            try:
                p_price = float(p_price) if p_price is not None else 0.0
            except (ValueError, TypeError):
                p_price = 0.0
        else:
            p_name = str(p)
            p_price = _extract_price(p_name)
        normalized_produits.append((_normalize_text(p_name), p_price))
    
    # Extraire les pièces visibles si des photos ont été fournies
    visible_pieces = None
    if photos_degats is not None:
        visible_pieces = photos_degats.get("pieces_endommagees", [])
        # Harmoniser en une liste de chaînes
        if not isinstance(visible_pieces, list):
            visible_pieces = []
            
    for zone, keywords in VEHICLE_ZONES.items():
        # 1. Déclaré (Constat)
        declared = False
        if any(kw in degats_constat for kw in keywords) or any(kw in choc_constat for kw in keywords):
            declared = True
            
        # 2. Facturé (Facture)
        invoiced = False
        montant = 0.0
        for p_norm, p_price in normalized_produits:
            if any(kw in p_norm for kw in keywords):
                invoiced = True
                montant += p_price
                
        # 3. Visible (Photos) - None si pas de photos, sinon bool
        visible = None
        if visible_pieces is not None:
            # Recherche exacte de la zone dans la liste renvoyée par le VLM
            visible = zone in visible_pieces

        # Détermination de la cohérence de la ligne
        ok = True
        if invoiced:
            if not declared:
                if visible is False:
                    # Facturé alors que non déclaré ET non visible -> Cas de fraude potentiel !
                    ok = False
                elif visible is True:
                    # Facturé et visible, mais oublié sur le constat -> anomalie de déclaration
                    ok = False
                elif visible is None:
                    # Pas de photos : règle de repli textuelle classique
                    ok = False
        elif visible is True and not declared:
            # Visible mais non déclaré ni facturé
            ok = False

        # On affiche la ligne dans le tableau si elle est déclarée, facturée ou visible
        if declared or invoiced or (visible is True):
            mapping.append({
                "zone": zone,
                "declared": declared,
                "invoiced": invoiced,
                "visible": visible,  # bool ou None
                "montant": montant if montant > 0 else None,
                "ok": ok
            })
            
    return mapping

def check_damages_coherence(normalized_dossier: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Génère les anomalies de cohérence dommages (constat vs facture vs photos).
    """
    anomalies: List[Dict[str, Any]] = []
    mapping = build_damage_mapping(normalized_dossier)
    
    # Savoir si les photos ont été soumises
    has_photos = normalized_dossier.get("photos_degats") is not None
    
    for item in mapping:
        zone = item["zone"]
        declared = item["declared"]
        invoiced = item["invoiced"]
        visible = item["visible"] # bool ou None
        
        if invoiced and not declared:
            if has_photos:
                if visible is False:
                    msg = (f"Suspicion de sur-facturation sur '{zone}' : composant facturé "
                           f"alors qu'aucun dégât n'est déclaré sur le constat ET qu'aucun dégât n'est visible sur les photos.")
                    anomalies.append({
                        "rule": "surfacturation_degat_non_visible",
                        "severity": "majeure",
                        "message": msg,
                        "detail": msg
                    })
                elif visible is True:
                    msg = (f"Le composant '{zone}' est facturé et visiblement endommagé sur les photos, "
                           f"mais il n'a pas été déclaré sur le constat amiable.")
                    anomalies.append({
                        "rule": "degat_facture_visible_non_declare",
                        "severity": "majeure",
                        "message": msg,
                        "detail": msg
                    })
                else:
                    # Cas théoriquement impossible si has_photos est True, mais par sécurité
                    msg = (f"Le composant '{zone}' est facturé alors qu'aucun dégât "
                           f"n'a été déclaré à cet endroit sur le constat.")
                    anomalies.append({
                        "rule": "degat_facture_non_declare",
                        "severity": "majeure",
                        "message": msg,
                        "detail": msg
                    })
            else:
                # Repli classique sans photos
                msg = (f"Le composant '{zone}' est réparé/facturé alors qu'aucun "
                       f"dégât n'a été déclaré à cet endroit sur le constat.")
                anomalies.append({
                    "rule": "degat_facture_non_declare",
                    "severity": "majeure",
                    "message": msg,
                    "detail": msg
                })
                
        elif visible is True and not declared and not invoiced:
            msg = (f"Dégât non déclaré : un dégât sur '{zone}' est visible sur les photos "
                   f"du véhicule, mais n'est ni mentionné dans le constat ni facturé.")
            anomalies.append({
                "rule": "degat_visible_non_declare",
                "severity": "mineure",
                "message": msg,
                "detail": msg
            })
            
    return anomalies
