import logging
from typing import Dict, List, Any

from app.coherence.schema import build_normalized_dossier
from app.coherence.identity_check import check_identity_coherence

logger = logging.getLogger(__name__)

def aggregate_report(raw_extracted: Dict[str, Dict[str, Any]], is_normalized: bool = False) -> Dict[str, Any]:
    """
    Builds the report dict expected by the frontend.
    """
    # 1. Normalize data if not already normalized
    if is_normalized:
        normalized = raw_extracted
    else:
        normalized = build_normalized_dossier(raw_extracted)

    # 2. Run checks
    from app.coherence.date_check import check_dates_coherence
    from app.coherence.damage_facture_check import check_damages_coherence, build_damage_mapping
    from app.coherence.amount_check import check_amounts_coherence

    anomalies = []
    anomalies.extend(check_identity_coherence(normalized))
    anomalies.extend(check_dates_coherence(normalized))
    anomalies.extend(check_damages_coherence(normalized))
    anomalies.extend(check_amounts_coherence(normalized))

    # 3. Build comparisons for the frontend
    comparisons = []
    
    # Identite conducteur
    constat_data = normalized.get('constat') or {}
    cin_data = normalized.get('cin') or {}
    permis_data = normalized.get('permis') or {}
    cg_data = normalized.get('carte_grise') or {}
    attestation_data = normalized.get('attestation') or {}
    
    constat_nom = f"{constat_data.get('conducteur_a_nom', '')} {constat_data.get('conducteur_a_prenom', '')}".strip()
    cin_nom = f"{cin_data.get('nom', '')} {cin_data.get('prenom', '')}".strip()
    permis_nom = f"{permis_data.get('nom', '')} {permis_data.get('prenom', '')}".strip()
    attest_nom = attestation_data.get('nom_prenom', '').strip()
    
    if cin_nom or permis_nom or constat_nom or attest_nom:
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
        if attest_nom:
            values["attestation"] = attest_nom
            docs.append("attestation")
            
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
    attest_immat = attestation_data.get("immatriculation")
    
    if constat_immat or cg_immat or attest_immat:
        values = {}
        docs = []
        if constat_immat:
            values["constat"] = constat_immat
            docs.append("constat")
        if cg_immat:
            values["carte_grise"] = cg_immat
            docs.append("carte_grise")
        if attest_immat:
            values["attestation"] = attest_immat
            docs.append("attestation")
            
        ok = True
        import re
        immat_list = []
        if constat_immat: immat_list.append(str(constat_immat))
        if cg_immat: immat_list.append(str(cg_immat))
        if attest_immat: immat_list.append(str(attest_immat))
        
        if len(immat_list) > 1:
            n1 = re.sub(r"[^A-Za-z0-9]", "", immat_list[0]).upper()
            for i in immat_list[1:]:
                n2 = re.sub(r"[^A-Za-z0-9]", "", i).upper()
                if n1 != n2:
                    ok = False
                    break
                
        comparisons.append({
            "field": "immatriculation",
            "label": "Immatriculation",
            "ok": ok,
            "docs": docs,
            "values": values
        })

    # Numéro de Permis
    constat_permis = constat_data.get("conducteur_a_permis")
    permis_num = permis_data.get("numero_permis")
    
    if constat_permis or permis_num:
        values = {}
        docs = []
        if constat_permis:
            values["constat"] = str(constat_permis)
            docs.append("constat")
        if permis_num:
            values["permis"] = str(permis_num)
            docs.append("permis")
            
        ok = True
        if constat_permis and permis_num:
            import re
            n1 = re.sub(r"\D", "", str(constat_permis))
            n2 = re.sub(r"\D", "", str(permis_num))
            if n1 and n2 and n1 != n2:
                ok = False
                
        comparisons.append({
            "field": "numero_permis",
            "label": "Numéro de Permis",
            "ok": ok,
            "docs": docs,
            "values": values
        })

    # Validité de l'assurance
    constat_validite_du = constat_data.get("assurance_validite_du")
    constat_validite_au = constat_data.get("assurance_validite_au")
    attest_validite_du = attestation_data.get("date_debut")
    attest_validite_au = attestation_data.get("date_fin")

    if (constat_validite_du or constat_validite_au) or (attest_validite_du or attest_validite_au):
        values = {}
        docs = []
        if constat_validite_du or constat_validite_au:
            values["constat"] = f"{constat_validite_du or '?'} → {constat_validite_au or '?'}"
            docs.append("constat")
        if attest_validite_du or attest_validite_au:
            values["attestation"] = f"{attest_validite_du or '?'} → {attest_validite_au or '?'}"
            docs.append("attestation")

        ok = True
        if (constat_validite_du or constat_validite_au) and (attest_validite_du or attest_validite_au):
            from app.coherence.date_check import parse_date
            c_du = parse_date(str(constat_validite_du)) if constat_validite_du else None
            c_au = parse_date(str(constat_validite_au)) if constat_validite_au else None
            a_du = parse_date(str(attest_validite_du)) if attest_validite_du else None
            a_au = parse_date(str(attest_validite_au)) if attest_validite_au else None

            if c_du and a_du and c_du != a_du:
                ok = False
            if c_au and a_au and c_au != a_au:
                ok = False
                
        comparisons.append({
            "field": "validite",
            "label": "Validité assurance au sinistre",
            "docs": docs,
            "values": values,
            "ok": ok
        })

    # Date de délivrance du permis
    constat_date_permis = constat_data.get("conducteur_a_permis_delivre")
    permis_date = permis_data.get("date_delivrance")
    
    if constat_date_permis or permis_date:
        values = {}
        docs = []
        if constat_date_permis:
            values["constat"] = str(constat_date_permis)
            docs.append("constat")
        if permis_date:
            values["permis"] = str(permis_date)
            docs.append("permis")
            
        ok = True
        if constat_date_permis and permis_date:
            from app.coherence.date_check import parse_date
            d1 = parse_date(str(constat_date_permis))
            d2 = parse_date(str(permis_date))
            if d1 and d2 and d1 != d2:
                ok = False
                
        comparisons.append({
            "field": "date_delivrance_permis",
            "label": "Date de Délivrance (Permis)",
            "ok": ok,
            "docs": docs,
            "values": values
        })

    # Marque / Type
    constat_marque = constat_data.get("marque_type_a")
    cg_constructeur = cg_data.get("constructeur")
    cg_type = cg_data.get("type_commercial")
    
    if constat_marque or cg_constructeur or cg_type:
        values = {}
        docs = []
        if constat_marque:
            values["constat"] = str(constat_marque)
            docs.append("constat")
        
        cg_marque_full = f"{cg_constructeur or ''} {cg_type or ''}".strip()
        if cg_marque_full:
            values["carte_grise"] = cg_marque_full
            docs.append("carte_grise")
            
        ok = True
        if constat_marque and cg_marque_full:
            from app.coherence.identity_check import _normalize_name, _similarity
            m1 = _normalize_name(constat_marque)
            m2 = _normalize_name(cg_marque_full)
            if m1 and m2:
                if not (m1 in m2 or m2 in m1 or _similarity(m1, m2) >= 0.5):
                    ok = False
                    
        comparisons.append({
            "field": "marque_type",
            "label": "Marque / Type de Véhicule",
            "ok": ok,
            "docs": docs,
            "values": values
        })

    # Numéro CIN
    cin_num = cin_data.get("numero_cin")
    cg_cin = cg_data.get("cin_ou_mf")
    
    if cin_num or cg_cin:
        values = {}
        docs = []
        if cin_num:
            values["cin"] = str(cin_num)
            docs.append("cin")
        if cg_cin:
            values["carte_grise"] = str(cg_cin)
            docs.append("carte_grise")
            
        ok = True
        if cin_num and cg_cin:
            import re
            n1 = re.sub(r"\D", "", str(cin_num))
            n2 = re.sub(r"\D", "", str(cg_cin))
            if n1 and n2 and len(n1) == 8 and len(n2) == 8 and n1 != n2:
                ok = False
                
        comparisons.append({
            "field": "numero_cin",
            "label": "Numéro de CIN",
            "ok": ok,
            "docs": docs,
            "values": values
        })

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
    
    # Build damage mapping for frontend
    damage_mapping = build_damage_mapping(normalized)
    
    return {
        "global": global_status,
        "extracted": flat_extracted,
        "comparisons": comparisons,
        "damageMapping": damage_mapping,
        "anomalies": anomalies,
    }
