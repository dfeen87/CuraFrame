# Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
"""
CuraFrame Chemical Interactions & Weakest Link Analysis Module.

Provides analytical capabilities to inspect chemical/physicochemical interactions,
coupled liabilities, and pinpoint the primary 'weakest link' (the critical safety
bottleneck or highest epistemic uncertainty) in a candidate Active Pharmaceutical
Ingredient (API). This helps medicinal chemists make drugs that are safe while
saving substantial early-stage design time.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from .core import Candidate, CuraFrame, EvaluationStatus, Severity, Constraint, ConstraintGroup

logger = logging.getLogger(__name__)


def calculate_safety_margin(comparator_name: str, threshold: Any, observed: Any) -> float:
    """
    Calculate the normalized safety margin of a parameter.

    A positive margin means the parameter is compliant (the larger the safer).
    A negative margin means the parameter violates the constraint (the more negative, the worse).
    """
    comp_lower = comparator_name.lower()

    # Standard numerical comparisons
    if "less_than" in comp_lower or "less" in comp_lower:
        if isinstance(threshold, (int, float)) and isinstance(observed, (int, float)):
            denom = abs(threshold) if threshold != 0.0 else 1.0
            return (threshold - observed) / denom

    elif "greater_than" in comp_lower or "greater" in comp_lower or "ratio_greater_than" in comp_lower:
        if isinstance(threshold, (int, float)) and isinstance(observed, (int, float)):
            denom = abs(threshold) if threshold != 0.0 else 1.0
            return (observed - threshold) / denom

    elif "within_range" in comp_lower:
        if isinstance(threshold, tuple) and len(threshold) == 2:
            lower, upper = threshold
            if isinstance(observed, (int, float)):
                denom = (upper - lower) if (upper - lower) != 0.0 else 1.0
                if observed < lower:
                    return (observed - lower) / denom
                elif observed > upper:
                    return (upper - observed) / denom
                else:
                    # Within range - safety margin is distance to nearest boundary
                    return min(observed - lower, upper - observed) / denom

    return 0.0


def get_chemical_strategies(parameter: str, action: str) -> List[str]:
    """
    Provide scientific, highly coherent structure-modification suggestions
    for drug candidates to address weak links, saving time in chemical synthesis.
    """
    param_lower = parameter.lower()

    if "herg" in param_lower:
        return [
            "Introduce polar substituents (e.g., fluoro, hydroxyl, or morpholine groups) to lower lipophilicity (logP).",
            "Reduce the basicity of the amine center by introducing electron-withdrawing groups nearby, or replacing the tertiary amine with an amide, sulfonamide, or urea linkage.",
            "Rigidify the molecular scaffold or alter the aromatic ring system (remove or substitute benzyl/phenethyl moieties) to disrupt the key π-π stacking interactions with hERG pore residues Tyr527 and Phe656."
        ]
    elif "logp" in param_lower:
        if action == "reduce":
            return [
                "Replace highly lipophilic aryl/alkyl groups with smaller cycloalkyl groups or polar heteroaromatic rings (e.g., pyridine, pyrimidine, oxadiazole).",
                "Introduce oxygen or nitrogen atoms into the carbon skeleton (e.g., replace an ether with a morpholine, or append solubilizing aliphatic chains with alcohol or ether functions).",
                "Utilize fluorinated substituents strategically (e.g., replacing CF3 with CHF2 or polar fluorine atoms) to fine-tune lipophilicity."
            ]
        elif action == "increase":
            return [
                "Add aliphatic carbon chains or bulky hydrophobic groups (e.g., t-butyl, cyclohexyl) to enhance partitioning into lipid membranes.",
                "Replace polar or ionizable substituents (like amines or carboxylic acids) with ester or amide bioisosteres.",
                "Incorporate aromatic substituents or halogen atoms (such as chlorine, bromine, or trifluoromethyl groups) to elevate logP."
            ]
    elif "cyp3a4" in param_lower:
        return [
            "Identify the metabolic soft spots (typically electron-rich aromatic rings or aliphatic methyl groups) and block them by introducing fluorine atoms or heavy isotopes.",
            "Lower candidate lipophilicity (logP) to diminish binding affinity to the highly hydrophobic active site of CYP3A4.",
            "Introduce conformational rigidity to restrict the compound from assuming the precise binding geometry required by the CYP3A4 catalytic pocket."
        ]
    elif "polar_surface_area" in param_lower or "psa" in param_lower:
        if action == "reduce":
            return [
                "Alkylate or mask hydrogen-bond donors (e.g., convert primary amines to secondary/tertiary, or methylate hydroxyl/amide functions).",
                "Design structural motifs that form intramolecular hydrogen bonds (IMHB), masking dynamic polar surface area in hydrophobic environments.",
                "Replace polar groups with bioisosteres that possess fewer polar atoms (e.g., replace a sulfone with a ketone)."
            ]
        elif action == "increase":
            return [
                "Append polar substituents containing nitrogen or oxygen (e.g., carboxylic acids, primary amides, sulfonamides).",
                "Replace hydrophobic carbon-carbon bonds with ether, ester, or amine linkages."
            ]
    elif "selectivity" in param_lower or "beta1" in param_lower:
        return [
            "Optimize the para-substituent on the phenoxypropanolamine or aryloxypropanolamine core, typical for selective β₁-adrenergic antagonists (e.g., atenolol/metoprolol structures), to establish hydrogen bonds with Asp138 in the β₁ receptor pocket.",
            "Introduce sterically hindered or specific amine substituents to prevent favorable binding inside the β₂ receptor pocket, maximizing β₁ selectivity and preventing asthma/bronchospasm triggers."
        ]
    elif "kd_5ht1a" in param_lower:
        return [
            "Incorporate or optimize an arylpiperazine or aminotetralin pharmacophore with an appropriate spacer length (typically 2-4 carbons) to ensure potent binding to the 5-HT₁ₐ GPCR pocket.",
            "Introduce a terminal imide, amide, or hydantoin group to form essential hydrogen bonds with Thr196 and Asp116."
        ]
    elif "kd_5ht2a" in param_lower or "kd_d2" in param_lower:
        return [
            "Introduce bulky steric block groups or disrupt the pharmacophoric spacing to dramatically reduce affinity for off-target dopamine D₂ or serotonin 5-HT₂ₐ receptors, avoiding EPS and psychotomimetic risks."
        ]
    elif "solubility" in param_lower:
        return [
            "Disrupt crystal lattice packing (which drives 'brick-dust' insolubility) by introducing molecular asymmetry or out-of-plane twist (e.g., ortho-substituents on aromatic rings).",
            "Incorporate basic or acidic ionizable centers to enable salt formation under physiological or formulation pH.",
            "Incorporate polar groups with high hydration capacity (e.g., polyethylene glycol chains, amino acids, or phosphate pro-drugs)."
        ]
    elif "half_life" in param_lower:
        return [
            "Replace metabolically unstable moieties (such as esters or unsubstituted aliphatic carbons) with amides or deuterated/fluorinated variants.",
            "Introduce steric shielding around vulnerable carbonyls or nitrogen atoms to retard enzymatic cleavage.",
            "Incorporate minor plasma protein binding elements to serve as a circulating depot, extending the pharmacokinetic half-life."
        ]
    return [
        "Consult bioisosteric database for target functional group replacements.",
        "Assess physicochemical parameters against standard Lead-Likeness and Rule of Five margins to balance target potency and ADMET safety."
    ]


def analyze_interactions(
    candidate: Candidate,
    framework: CuraFrame,
    population: Optional[str] = None,
    strict: bool = True
) -> Dict[str, Any]:
    """
    Perform a deep scientific analysis of candidate chemical interactions and its weakest link.

    Args:
        candidate: The Candidate API design to analyze.
        framework: The CuraFrame reasoning instance containing constraints.
        population: Optional patient population context.
        strict: If True, missing properties -> INDETERMINATE.

    Returns:
        A dictionary containing:
          - candidate_name: str
          - status: str (accepted, rejected, indeterminate)
          - margins: list of detailed constraint safety margin evaluations
          - physical_weakest_link: primary safety bottleneck or failure point
          - epistemic_weakest_link: constraint with the lowest scientific confidence
          - coupled_risks: synergistic interactions (such as Cardiotoxicity, DDI, and CNS balance)
          - optimization_recommendations: concrete structure-modification ideas to save design time
    """
    # Evaluate candidate using standard CuraFrame evaluation
    eval_result = framework.evaluate(candidate, population=population, strict=strict)

    # Retrieve constraints with population adjustments applied
    constraints = framework.population_stratifier.apply(population, framework.safety_constraints)

    margins_list = []

    def _gather_constraints_recursive(item: Union[Constraint, ConstraintGroup]):
        res = []
        if isinstance(item, Constraint):
            res.append(item)
        elif isinstance(item, ConstraintGroup):
            for child in item.children:
                res.extend(_gather_constraints_recursive(child))
        return res

    flat_constraints: List[Constraint] = []
    for c_item in constraints:
        flat_constraints.extend(_gather_constraints_recursive(c_item))

    for c in flat_constraints:
        val = candidate.get(c.name)
        if val is None:
            continue

        satisfied = False
        try:
            satisfied = c.evaluate(val)
        except Exception:
            pass

        comp_name = c.comparator.__name__ if hasattr(c.comparator, "__name__") else str(c.comparator)
        margin = calculate_safety_margin(comp_name, c.threshold, val)

        confidence = c.provenance.confidence if c.provenance else 1.0
        rationale = c.rationale

        margins_list.append({
            "name": c.name,
            "observed": val,
            "threshold": c.threshold,
            "margin": margin,
            "satisfied": satisfied,
            "severity": c.severity,
            "confidence": confidence,
            "rationale": rationale
        })

    # Sort margins to find the physical weakest link
    # Violating parameters are sorted by worst margin first (most negative).
    # Compliant parameters are sorted by closest to boundary first (smallest positive margin).
    violating = [m for m in margins_list if not m["satisfied"]]
    compliant = [m for m in margins_list if m["satisfied"]]

    physical_weakest_link = None
    if violating:
        # Worst violation: most negative margin
        violating.sort(key=lambda x: x["margin"])
        physical_weakest_link = violating[0]
    elif compliant:
        # Tightest margin: smallest positive margin
        compliant.sort(key=lambda x: x["margin"])
        physical_weakest_link = compliant[0]

    # Find epistemic weakest link (lowest confidence score)
    epistemic_weakest_link = None
    if margins_list:
        margins_sorted_by_confidence = sorted(margins_list, key=lambda x: x["confidence"])
        epistemic_weakest_link = margins_sorted_by_confidence[0]

    # Coupled / Synergistic Risk Analysis
    coupled_risks = []

    logP_val = candidate.get("logP")
    herg_val = candidate.get("hERG_IC50")
    cyp_val = candidate.get("CYP3A4_IC50")
    psa_val = candidate.get("polar_surface_area")
    sol_val = candidate.get("aqueous_solubility")

    # 1. Lipophilicity-hERG Cardiotoxicity Synergy
    if logP_val is not None and herg_val is not None:
        effective_logp = max(0.1, logP_val)
        raw_score = effective_logp * (10.0 / max(1.0, herg_val))
        score = min(10.0, max(0.0, raw_score))

        # Adjust level based on thresholds and scores
        if score >= 7.0 or (logP_val > 3.5 and herg_val < 15.0):
            level = "HIGH"
            desc = ("High lipophilicity (logP) combined with low hERG IC50 synergistically escalates cardiotoxicity risk. "
                    "Hydrophobic candidates partition extensively into cardiac membranes and bind more stably to key aromatic "
                    "residues (Tyr527 and Phe656) within the hERG channel pore, dramatically increasing QTc prolongation liabilities.")
        elif score >= 4.0:
            level = "MODERATE"
            desc = ("Moderate cardiotoxicity risk detected. The lipophilic profile of this compound is high enough to facilitate "
                    "membrane partitioning, which might potentiate hERG channel blockade even at moderate IC50 levels.")
        else:
            level = "LOW"
            desc = "Low synergistic cardiotoxicity risk. Lipophilicity and hERG IC50 values remain in a well-tolerated, safe range."

        coupled_risks.append({
            "name": "Lipophilic Cardiotoxicity Synergy (hERG vs logP)",
            "score": round(score, 2),
            "level": level,
            "description": desc,
            "parameters_involved": ["logP", "hERG_IC50"]
        })

    # 2. Lipophilicity-CYP3A4 DDI Liability
    if logP_val is not None and cyp_val is not None:
        effective_logp = max(0.1, logP_val)
        raw_score = effective_logp * (10.0 / max(1.0, cyp_val))
        score = min(10.0, max(0.0, raw_score))

        if score >= 7.0 or (logP_val > 3.5 and cyp_val < 10.0):
            level = "HIGH"
            desc = ("Potent CYP3A4 inhibition coupled with high logP creates a severe drug-drug interaction (DDI) liability. "
                    "Hydrophobic compounds easily fit into and block the large, hydrophobic binding pocket of the CYP3A4 enzyme, "
                    "leading to metabolic stagnation and systemic accumulation of co-administered therapeutics.")
        elif score >= 4.0:
            level = "MODERATE"
            desc = ("Moderate DDI liability. Compound exhibits moderate CYP3A4 affinity that is amplified by lipophilic active-site partitioning.")
        else:
            level = "LOW"
            desc = "Low drug-drug interaction risk. Compound is highly unlikely to cause metabolic liabilities or statin/antihypertensive interactions."

        coupled_risks.append({
            "name": "Lipophilic DDI Liability (CYP3A4 vs logP)",
            "score": round(score, 2),
            "level": level,
            "description": desc,
            "parameters_involved": ["logP", "CYP3A4_IC50"]
        })

    # 3. CNS MPO / BBB Permeability Balance
    if logP_val is not None and psa_val is not None:
        logp_dev = max(0.0, 2.0 - logP_val) + max(0.0, logP_val - 3.5)
        psa_dev = max(0.0, 40.0 - psa_val) + max(0.0, psa_val - 80.0)
        raw_score = (logp_dev * 2.0) + (psa_dev / 10.0)
        score = min(10.0, max(0.0, raw_score))

        if score >= 5.0:
            level = "HIGH"
            desc = ("Substantial deviation from the CNS Multiparameter Optimization (MPO) window. "
                    "Either high polar surface area (PSA) blocks blood-brain barrier (BBB) crossing, "
                    "or excessive lipophilicity leads to high non-specific brain tissue binding and P-gp efflux liability.")
        elif score >= 2.0:
            level = "MODERATE"
            desc = ("Moderate deviation from ideal CNS design space. Minor structural modifications could significantly "
                    "enhance CNS distribution or peripheral-only selectivity.")
        else:
            level = "LOW"
            desc = "Favorable CNS MPO profile. The compound balances moderate lipophilicity and polarity, indicating strong potential for BBB permeability."

        coupled_risks.append({
            "name": "CNS-MPO Balance (logP vs polar_surface_area)",
            "score": round(score, 2),
            "level": level,
            "description": desc,
            "parameters_involved": ["logP", "polar_surface_area"]
        })

    # 4. Physicochemical Solubility Risk
    if logP_val is not None and sol_val is not None:
        if logP_val > 4.0 and sol_val < 10.0:
            score = 8.5
            level = "HIGH"
            desc = ("Classic 'Grease-ball' pharmacokinetic profile. Elevated lipophilicity and poor aqueous solubility "
                    "obstruct oral drug dissolution in the gastrointestinal tract, risking erratic bioavailability and food effects.")
        elif logP_val < 1.0 and sol_val < 10.0:
            score = 7.5
            level = "HIGH"
            desc = ("Classic 'Brick-dust' pharmacokinetic profile. The compound's insolubility is likely governed by "
                    "high crystal lattice energy rather than lipophilicity, making formulation extremely difficult without sacrificing cell permeability.")
        elif sol_val < 20.0:
            score = 4.5
            level = "MODERATE"
            desc = "Moderate solubility risk. Solid dispersion, co-solvent, or salt screening formulation strategies may be necessary."
        else:
            score = 1.0
            level = "LOW"
            desc = "Excellent solubility profile. Low risk of dissolution-rate limited absorption or parenteral formulation barriers."

        coupled_risks.append({
            "name": "Physicochemical Solubility Risk",
            "score": score,
            "level": level,
            "description": desc,
            "parameters_involved": ["logP", "aqueous_solubility"]
        })

    # Synthesis/Optimization Recommendations based on weakest links
    recommendations = []
    if physical_weakest_link:
        p_name = physical_weakest_link["name"]
        satisfied = physical_weakest_link["satisfied"]
        margin = physical_weakest_link["margin"]

        action = "modify"
        if not satisfied:
            action = "reduce" if margin < 0 and "less_than" in str(physical_weakest_link.get("comparator", "less_than_or_equal")) else "increase"
        else:
            # For accepted parameters, identify standard directional recommendation based on name
            if "herg" in p_name.lower() or "ic50" in p_name.lower():
                action = "increase"
            elif "logp" in p_name.lower():
                action = "reduce" if physical_weakest_link["observed"] > 3.0 else "modify"
            elif "solubility" in p_name.lower():
                action = "increase"

        recommendations.append({
            "parameter": p_name,
            "action": action,
            "rationale": f"Address primary physical weakest link: observed {physical_weakest_link['observed']} vs threshold {physical_weakest_link['threshold']}.",
            "chemical_strategies": get_chemical_strategies(p_name, action)
        })

    # If epistemic weakest link is different, add its suggestions too
    if epistemic_weakest_link and (not physical_weakest_link or epistemic_weakest_link["name"] != physical_weakest_link["name"]):
        recommendations.append({
            "parameter": epistemic_weakest_link["name"],
            "action": "verify",
            "rationale": f"Identified as the logical/epistemic weakest link in our scientific reasoning with lowest confidence ({epistemic_weakest_link['confidence']:.2f}).",
            "chemical_strategies": [
                f"Conduct focused in vitro assays or high-level quantum mechanical modeling to confirm the exact value of {epistemic_weakest_link['name']}.",
                "Refer to additional regulatory guidelines or scientific literature to tighten safety assumptions and validate constraint provenance."
            ]
        })

    return {
        "candidate_name": candidate.name,
        "status": eval_result.status.value,
        "margins": margins_list,
        "physical_weakest_link": physical_weakest_link,
        "epistemic_weakest_link": epistemic_weakest_link,
        "coupled_risks": coupled_risks,
        "optimization_recommendations": recommendations
    }
