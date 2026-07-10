import logging
from typing import Dict, List, Any

from app.coherence.schema import build_normalized_dossier
from app.coherence.identity_check import check_identity_coherence

logger = logging.getLogger(__name__)

def aggregate_report(raw_extracted: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Builds the report dict expected by the frontend.
    """
    # 1. Normalize data
    normalized = build_normalized_dossier(raw_extracted)

    # 2. Run checks
    anomalies = []
    anomalies.extend(check_identity_coherence(normalized))

    # Add a mock anomaly if we want to test incoherence based on missing data
    # (Optional, but let's stick to the real checks for now)

    # 3. Build comparisons for the frontend
    comparisons = []
    
    # Identite conducteur
    constat_data = normalized.get('constat') or {}
    cin_data = normalized.get('cin') or {}
    permis_data = normalized.get('permis') or {}
    cg_data = normalized.get('carte_grise') or {}
    
    constat_nom = f"{constat_data.get('conducteur_a_nom', '')} {constat_data.get('conducteur_a_prenom', '')}".strip()
    cin_nom = f"{cin_data.get('nom', '')} {cin_data.get('prenom', '')}".strip()
    permis_nom = f"{permis_data.get('nom', '')} {permis_data.get('prenom', '')}".strip()
    
    if cin_nom or permis_nom or constat_nom:
        values = {}
        docs = []
        if constat_nom:
            values["constat"] = constat_nom
            docs.append("constat")
        if cin_nom:
            values["cin"] = cin_nom
            docs.append("cin")
        if permis_nom:
            values["permis"] = permis_nom
            docs.append("permis")
            
        # Check if they match loosely
        ok = True
        if len(docs) > 1:
            from app.coherence.identity_check import _names_match
            base = values[docs[0]]
            for d in docs[1:]:
                if not _names_match(base, values[d]):
                    ok = False
                    break
                    
        comparisons.append({
            "field": "identite",
            "label": "Identité du conducteur",
            "ok": ok,
            "docs": docs,
            "values": values
        })

    # Immatriculation
    constat_immat = constat_data.get("immatriculation_a")
    cg_immat = cg_data.get("immatriculation")
    
    if constat_immat or cg_immat:
        values = {}
        docs = []
        if constat_immat:
            values["constat"] = constat_immat
            docs.append("constat")
        if cg_immat:
            values["carte_grise"] = cg_immat
            docs.append("carte_grise")
            
        ok = True
        if constat_immat and cg_immat:
            import re
            n1 = re.sub(r"[^A-Za-z0-9]", "", str(constat_immat)).upper()
            n2 = re.sub(r"[^A-Za-z0-9]", "", str(cg_immat)).upper()
            if n1 != n2:
                ok = False
                
        comparisons.append({
            "field": "immatriculation",
            "label": "Immatriculation",
            "ok": ok,
            "docs": docs,
            "values": values
        })

    # 4. Build a flattened extracted dict for the frontend view
    flat_extracted = {}
    for doc_key, data in normalized.items():
        if not data:
            continue
        flat_doc = {}
        for k, v in data.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float)):
                flat_doc[k] = str(v)
            elif isinstance(v, list):
                flat_doc[k] = [str(item) for item in v]
            elif isinstance(v, dict):
                # Don't show deeply nested in the flat view
                pass
        if flat_doc:
            flat_extracted[doc_key] = flat_doc

    global_status = "coherent" if not anomalies else "a_verifier"
    
    # Optional damage mapping for frontend
    damage_mapping = []
    
    return {
        "global": global_status,
        "extracted": flat_extracted,
        "comparisons": comparisons,
        "damageMapping": damage_mapping,
        "anomalies": anomalies,
    }
