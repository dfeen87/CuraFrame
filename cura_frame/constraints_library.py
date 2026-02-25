"""
CuraFrame Constraint Library

Canonical definitions of commonly used safety and design constraints.

This module contains:
- Named constraint definitions
- Human-readable rationales
- Conservative default thresholds
- Explicit provenance metadata

This module contains NO evaluation logic.
All constraints must be evaluated through CuraFrame core.

Philosophy:
    Constraints encode known limits.
    They are not suggestions, targets, or optimizations.
    Default values are intentionally conservative.
    Tightening is safer than loosening.
"""

from typing import List, Tuple

from .core import Constraint, Severity, Provenance
from .comparators import (
    less_than_or_equal,
    greater_than_or_equal,
    within_range,
    ratio_greater_than,
)


# ---------------------------------------------------------------------
# Physicochemical constraints (ADMET predictors)
# ---------------------------------------------------------------------

def logP_max(max_logP: float = 4.0) -> Constraint:
    """
    Maximum allowable lipophilicity (logP).

    Rationale:
        Excessive lipophilicity is associated with:
        - hERG liability
        - promiscuous off-target binding
        - poor aqueous solubility
        - unpredictable tissue distribution
        - metabolic instability

    Default threshold (4.0) is intentionally conservative.
    For CNS-active compounds, consider 3.5-3.8.

    References:
        Lipinski et al. (1997) - Rule of Five
        Waring (2010) - Lipophilicity in drug discovery
    """
    return Constraint(
        name="logP",
        threshold=max_logP,
        comparator=less_than_or_equal,
        rationale="Excessive lipophilicity increases off-target and cardiac risk",
        severity=Severity.CRITICAL,
        provenance=Provenance(
            source_type="medicinal_chemistry_guideline",
            confidence=0.9,
            references=[
                "doi:10.1016/S0169-409X(96)00423-1",  # Lipinski
                "doi:10.1517/17460441.2010.533654"    # Waring
            ]
        )
    )


def logP_range(min_logP: float = 1.0, max_logP: float = 4.0) -> Constraint:
    """
    Acceptable lipophilicity range.

    Rationale:
        Too low: poor membrane permeability
        Too high: toxicity, off-target effects

    Use this for compounds requiring oral bioavailability
    with moderate CNS exposure.
    """
    return Constraint(
        name="logP",
        threshold=(min_logP, max_logP),
        comparator=within_range,
        rationale="logP outside this range reduces bioavailability or increases risk",
        severity=Severity.SEVERE,
        provenance=Provenance(
            source_type="medicinal_chemistry_guideline",
            confidence=0.85,
            references=["doi:10.1016/S0169-409X(96)00423-1"]
        )
    )


def molecular_weight_range(
    min_mw: float = 150.0,
    max_mw: float = 500.0
) -> Constraint:
    """
    Acceptable molecular weight range (Da).

    Rationale:
        MW < 150: Often too reactive, nonspecific
        MW > 500: Reduced permeability, oral absorption issues

    For CNS drugs, consider max_mw = 450 Da.
    For biologics-inspired scaffolds, this constraint may not apply.

    References:
        Lipinski et al. (1997)
        Veber et al. (2002) - oral bioavailability
    """
    return Constraint(
        name="molecular_weight",
        threshold=(min_mw, max_mw),
        comparator=within_range,
        rationale="Molecular weight outside this range reduces drug-like behavior",
        severity=Severity.SEVERE,
        provenance=Provenance(
            source_type="drug_likeness_guideline",
            confidence=0.85,
            references=[
                "doi:10.1016/S0169-409X(96)00423-1",
                "doi:10.1021/jm020017n"
            ]
        )
    )


def polar_surface_area_max(max_psa: float = 90.0) -> Constraint:
    """
    Maximum polar surface area (PSA, Ų).

    Rationale:
        PSA > 90 Ų: significantly reduced membrane permeability
        PSA > 140 Ų: oral absorption unlikely

    For CNS-penetrant drugs, use 70-80 Ų.
    For peripheral-only drugs, this can be relaxed to 140 Ų.

    References:
        Pajouhesh & Lenz (2005) - CNS drug design
        Wager et al. (2010) - CNS MPO
    """
    return Constraint(
        name="polar_surface_area",
        threshold=max_psa,
        comparator=less_than_or_equal,
        rationale="High polar surface area reduces membrane permeability",
        severity=Severity.SEVERE,
        provenance=Provenance(
            source_type="cns_drug_design_guideline",
            confidence=0.85,
            references=[
                "doi:10.1602/neurorx.2.4.541",
                "doi:10.1021/cn100007x"
            ]
        )
    )


def hydrogen_bond_donors_max(max_hbd: int = 5) -> Constraint:
    """
    Maximum number of hydrogen bond donors (NH, OH).

    Rationale:
        Excessive HBD reduces membrane permeability.
        Part of Lipinski's Rule of Five.

    For CNS drugs, consider max_hbd = 2.
    """
    return Constraint(
        name="hydrogen_bond_donors",
        threshold=max_hbd,
        comparator=less_than_or_equal,
        rationale="Excessive hydrogen bond donors reduce permeability",
        severity=Severity.WARNING,
        provenance=Provenance(
            source_type="drug_likeness_guideline",
            confidence=0.85,
            references=["doi:10.1016/S0169-409X(96)00423-1"]
        )
    )


def hydrogen_bond_acceptors_max(max_hba: int = 10) -> Constraint:
    """
    Maximum number of hydrogen bond acceptors (N, O).

    Rationale:
        Excessive HBA reduces permeability.
        Part of Lipinski's Rule of Five.

    For CNS drugs, consider max_hba = 7.
    """
    return Constraint(
        name="hydrogen_bond_acceptors",
        threshold=max_hba,
        comparator=less_than_or_equal,
        rationale="Excessive hydrogen bond acceptors reduce permeability",
        severity=Severity.WARNING,
        provenance=Provenance(
            source_type="drug_likeness_guideline",
            confidence=0.85,
            references=["doi:10.1016/S0169-409X(96)00423-1"]
        )
    )


# ---------------------------------------------------------------------
# CNS exposure constraints
# ---------------------------------------------------------------------

def cns_mpo_logP(max_logP: float = 3.8) -> Constraint:
    """
    CNS multiparameter optimization (MPO) - logP component.

    Rationale:
        For CNS-active drugs, logP should be lower than
        general medicinal chemistry guidelines to reduce
        off-target CNS effects and improve safety margin.

    References:
        Wager et al. (2010) - CNS MPO score
    """
    return Constraint(
        name="logP",
        threshold=max_logP,
        comparator=less_than_or_equal,
        rationale="CNS drugs require lower logP for safety and selectivity",
        severity=Severity.CRITICAL,
        provenance=Provenance(
            source_type="cns_drug_design_guideline",
            confidence=0.85,
            references=["doi:10.1021/cn100007x"]
        )
    )


def cns_psa_range(min_psa: float = 40.0, max_psa: float = 80.0) -> Constraint:
    """
    CNS-optimized polar surface area range.

    Rationale:
        PSA < 40: May have excessive CNS penetration, off-target effects
        PSA > 80: Reduced BBB penetration

    This range balances efficacy and safety for centrally acting drugs.
    """
    return Constraint(
        name="polar_surface_area",
        threshold=(min_psa, max_psa),
        comparator=within_range,
        rationale="CNS drugs require balanced PSA for BBB penetration and safety",
        severity=Severity.SEVERE,
        provenance=Provenance(
            source_type="cns_drug_design_guideline",
            confidence=0.80,
            references=[
                "doi:10.1021/cn100007x",
                "doi:10.1016/S1474-4422(24)00476-9"
            ]
        )
    )


def bbb_penetration_logP_psa(
    logP_range_: Tuple[float, float] = (2.0, 4.0),
    psa_max_: float = 90.0
) -> List[Constraint]:
    """
    Combined BBB penetration criteria.

    Returns both logP range and PSA constraints optimized
    for blood-brain barrier crossing.

    Use for: CNS-active therapeutics requiring brain exposure.
    """
    return [
        Constraint(
            name="logP",
            threshold=logP_range_,
            comparator=within_range,
            rationale="BBB penetration requires moderate lipophilicity",
            severity=Severity.SEVERE,
            provenance=Provenance(
                source_type="bbb_permeability_study",
                confidence=0.80,
                references=["doi:10.1016/S1474-4422(24)00476-9"]
            )
        ),
        Constraint(
            name="polar_surface_area",
            threshold=psa_max_,
            comparator=less_than_or_equal,
            rationale="High PSA blocks BBB penetration",
            severity=Severity.SEVERE,
            provenance=Provenance(
                source_type="bbb_permeability_study",
                confidence=0.80,
                references=["doi:10.1016/S1474-4422(24)00476-9"]
            )
        )
    ]


# ---------------------------------------------------------------------
# Cardiac safety constraints
# ---------------------------------------------------------------------

def hERG_ic50_min(min_ic50_uM: float = 10.0) -> Constraint:
    """
    Minimum acceptable hERG IC50 (μM).

    Rationale:
        hERG channel block causes QT interval prolongation,
        which can lead to torsades de pointes and sudden cardiac death.

        IC50 < 10 μM: High risk
        IC50 10-30 μM: Moderate risk, requires caution
        IC50 > 30 μM: Generally acceptable

    Default threshold (10 μM) is intentionally conservative.
    For vulnerable populations (elderly, cardiac comorbidity),
    use 15-20 μM.

    References:
        Redfern et al. (2003) - hERG and QT
        ICH S7B Guidelines
    """
    return Constraint(
        name="hERG_IC50",
        threshold=min_ic50_uM,
        comparator=greater_than_or_equal,
        rationale="Low hERG IC50 increases QT prolongation and sudden cardiac death risk",
        severity=Severity.CRITICAL,
        provenance=Provenance(
            source_type="in_vitro_safety_pharmacology",
            confidence=0.9,
            references=[
                "doi:10.1093/cvr/58.1.32",
                "ICH_S7B"
            ]
        )
    )


def qtc_prolongation_risk_low() -> Constraint:
    """
    Constraint for clinical QTc prolongation risk.

    Rationale:
        ΔQTc > 20 ms: requires regulatory scrutiny
        ΔQTc > 30 ms: high risk, often unacceptable

    Use when clinical QTc data is available.
    For preclinical, use hERG_ic50_min instead.
    """
    return Constraint(
        name="delta_QTc_ms",
        threshold=20.0,
        comparator=less_than_or_equal,
        rationale="QTc prolongation >20ms increases arrhythmia risk",
        severity=Severity.CRITICAL,
        provenance=Provenance(
            source_type="clinical_cardiology",
            confidence=0.95,
            references=[
                "ICH_E14",
                "doi:10.1093/eurheartj/ehad708"
            ]
        )
    )


# ---------------------------------------------------------------------
# Receptor selectivity constraints
# ---------------------------------------------------------------------

def beta1_over_beta2_selectivity_min(
    min_selectivity: float = 100.0
) -> Constraint:
    """
    Minimum β₁/β₂ selectivity ratio (Kd_β₂ / Kd_β₁).

    Rationale:
        β₂ antagonism causes:
        - Bronchoconstriction
        - Asthma exacerbation
        - Reduced exercise tolerance

    Selectivity requirements:
        50x: Marginal, use with caution
        100x: Standard for cardioselective β-blockers
        200x: Preferred for asthmatics

    For CardiAnx-1, 100x is baseline; 200x for asthmatic populations.

    References:
        Baker (2005) - β-adrenoceptor selectivity
        Bangalore & Steg (2024) - modern β-blocker use
    """
    return Constraint(
        name="beta1_selectivity",
        threshold=min_selectivity,
        comparator=ratio_greater_than,
        rationale="Insufficient β₁/β₂ selectivity increases bronchospasm risk",
        severity=Severity.SEVERE,
        provenance=Provenance(
            source_type="clinical_pharmacology",
            confidence=0.8,
            references=[
                "doi:10.1111/j.1476-5381.2005.00048.x",
                "doi:10.1093/eurheartj/ehad708"
            ]
        )
    )


def serotonin_5ht1a_affinity_range(
    min_Kd_nM: float = 5.0,
    max_Kd_nM: float = 20.0
) -> Constraint:
    """
    Target 5-HT₁ₐ affinity range for anxiolytic effect.

    Rationale:
        Kd < 5 nM: Risk of excessive agonism, sedation
        Kd > 20 nM: Insufficient anxiolytic efficacy
        Optimal: 10-15 nM for partial agonism

    Use for: Central anxiolytics targeting 5-HT₁ₐ receptors.

    References:
        Yohn et al. (2017) - 5-HT receptors in depression
    """
    return Constraint(
        name="Kd_5HT1A",
        threshold=(min_Kd_nM, max_Kd_nM),
        comparator=within_range,
        rationale="5-HT₁ₐ affinity must balance efficacy and side effects",
        severity=Severity.SEVERE,
        provenance=Provenance(
            source_type="pharmacology_literature",
            confidence=0.75,
            references=["doi:10.1186/s13041-017-0306-y"]
        )
    )


def off_target_5ht2a_avoidance(max_affinity_nM: float = 500.0) -> Constraint:
    """
    Maximum acceptable 5-HT₂ₐ affinity (higher Kd = weaker binding).

    Rationale:
        5-HT₂ₐ agonism can cause:
        - Hallucinations
        - Psychotomimetic effects
        - Sleep disruption

    Kd > 500 nM is considered weak enough to avoid these effects.

    Use for: Serotonergic agents where 5-HT₂ₐ is not the target.
    """
    return Constraint(
        name="Kd_5HT2A",
        threshold=max_affinity_nM,
        comparator=greater_than_or_equal,
        rationale="Strong 5-HT₂ₐ binding increases psychotomimetic risk",
        severity=Severity.SEVERE,
        provenance=Provenance(
            source_type="pharmacology_literature",
            confidence=0.80,
            references=["doi:10.1186/s13041-017-0306-y"]
        )
    )


def dopamine_d2_avoidance(max_affinity_nM: float = 1000.0) -> Constraint:
    """
    Maximum acceptable D₂ dopamine receptor affinity.

    Rationale:
        D₂ antagonism causes:
        - Extrapyramidal symptoms (EPS)
        - Akathisia
        - Prolactin elevation
        - Cognitive side effects

    Kd > 1000 nM (1 μM) is generally considered safe.

    Use for: Non-antipsychotic CNS agents.
    """
    return Constraint(
        name="Kd_D2",
        threshold=max_affinity_nM,
        comparator=greater_than_or_equal,
        rationale="D₂ antagonism increases extrapyramidal side effects",
        severity=Severity.SEVERE,
        provenance=Provenance(
            source_type="pharmacology_literature",
            confidence=0.85,
            references=["PMID:12629530"]
        )
    )


# ---------------------------------------------------------------------
# Pharmacokinetic constraints
# ---------------------------------------------------------------------

def plasma_half_life_range(
    min_t_half_hours: float = 4.0,
    max_t_half_hours: float = 24.0
) -> Constraint:
    """
    Acceptable plasma half-life range (hours).

    Rationale:
        t½ < 4h: Requires frequent dosing, poor compliance
        t½ > 24h: Accumulation risk, slow titration

    For once-daily dosing: 8-16 hours optimal
    For twice-daily: 4-8 hours acceptable

    References:
        General PK principles
    """
    return Constraint(
        name="plasma_half_life",
        threshold=(min_t_half_hours, max_t_half_hours),
        comparator=within_range,
        rationale="Half-life outside this range complicates dosing or increases risk",
        severity=Severity.WARNING,
        provenance=Provenance(
            source_type="pharmacokinetics",
            confidence=0.70,
            references=["pharmacokinetics_textbook"]
        )
    )


def oral_bioavailability_min(min_F_percent: float = 30.0) -> Constraint:
    """
    Minimum acceptable oral bioavailability (%).

    Rationale:
        F < 30%: High inter-patient variability, difficult dosing
        F > 50%: Generally acceptable
        F > 70%: Excellent

    Default 30% is conservative for early-stage filtering.

    Use for: Oral drug candidates only.
    """
    return Constraint(
        name="oral_bioavailability",
        threshold=min_F_percent,
        comparator=greater_than_or_equal,
        rationale="Low bioavailability complicates dosing and increases variability",
        severity=Severity.WARNING,
        provenance=Provenance(
            source_type="pharmacokinetics",
            confidence=0.65,
            references=["pharmacokinetics_textbook"]
        )
    )


# ---------------------------------------------------------------------
# Metabolic stability constraints
# ---------------------------------------------------------------------

def hepatic_clearance_max(max_CL_mL_min_kg: float = 50.0) -> Constraint:
    """
    Maximum acceptable hepatic clearance rate (mL/min/kg).

    Rationale:
        High clearance → short half-life → frequent dosing
        Liver blood flow ≈ 20 mL/min/kg, so CL > 50 is very high

    Use when: In vivo clearance data is available.
    """
    return Constraint(
        name="hepatic_clearance",
        threshold=max_CL_mL_min_kg,
        comparator=less_than_or_equal,
        rationale="High hepatic clearance reduces half-life and requires frequent dosing",
        severity=Severity.WARNING,
        provenance=Provenance(
            source_type="pharmacokinetics",
            confidence=0.70,
            references=["pharmacokinetics_textbook"]
        )
    )


# ---------------------------------------------------------------------
# Metabolic safety constraints
# ---------------------------------------------------------------------

def cyp3a4_inhibition_min(min_ic50_uM: float = 10.0) -> Constraint:
    """
    Minimum acceptable CYP3A4 IC50 (μM).

    Rationale:
        CYP3A4 is the most abundant hepatic metabolic enzyme and is
        responsible for metabolising ~50% of clinically used drugs.
        Inhibition causes drug-drug interactions (DDIs), toxicity, and
        unpredictable pharmacokinetics.

        IC50 < 1 μM: High DDI risk — generally unacceptable
        IC50 1–10 μM: Moderate risk — requires caution
        IC50 > 10 μM: Generally acceptable for early-stage candidates

    References:
        Isoherranen et al. (2009) — CYP3A4 and DDI prediction
        FDA Guidance on Drug Interaction Studies (2020)
    """
    return Constraint(
        name="CYP3A4_IC50",
        threshold=min_ic50_uM,
        comparator=greater_than_or_equal,
        rationale="CYP3A4 inhibition causes drug-drug interactions and metabolic toxicity",
        severity=Severity.CRITICAL,
        provenance=Provenance(
            source_type="in_vitro_metabolic_safety",
            confidence=0.85,
            references=[
                "doi:10.1124/dmd.109.028431",
                "FDA_DDI_Guidance_2020"
            ]
        )
    )


def therapeutic_index_min(min_ti: float = 10.0) -> Constraint:
    """
    Minimum acceptable therapeutic index (TI = TD50 / ED50).

    Rationale:
        The therapeutic index quantifies the safety window between
        the effective dose and the toxic dose.

        TI < 2: Narrow — high clinical risk, requires TDM
        TI 2–10: Moderate — manageable with careful dosing
        TI > 10: Acceptable for most therapeutic contexts

    Default (10.0) is conservative for non-oncology compounds.
    For cytotoxic oncology agents, a lower minimum may be appropriate
    with strict population monitoring.

    References:
        Muller & Milton (2012) — The determination and interpretation of TI
    """
    return Constraint(
        name="therapeutic_index",
        threshold=min_ti,
        comparator=greater_than_or_equal,
        rationale="Low therapeutic index increases risk of toxicity at therapeutic doses",
        severity=Severity.CRITICAL,
        provenance=Provenance(
            source_type="preclinical_safety_pharmacology",
            confidence=0.80,
            references=[
                "doi:10.1038/nrd3801"
            ]
        )
    )


def protein_binding_max(max_ppb_percent: float = 95.0) -> Constraint:
    """
    Maximum acceptable plasma protein binding (PPB, %).

    Rationale:
        Only unbound (free) drug crosses membranes and exerts
        pharmacological effects. Highly bound compounds exhibit:
        - High inter-patient variability (hypoalbuminaemia risk)
        - Displacement interactions at high binding sites
        - Unpredictable dose-response relationships

        PPB > 99%: Very high — clinically problematic
        PPB > 95%: High — requires characterisation
        PPB < 95%: Generally acceptable

    Use for: All drug modalities, particularly those with narrow TI.

    References:
        Schmidt et al. (2010) — PPB and drug discovery
    """
    return Constraint(
        name="protein_binding",
        threshold=max_ppb_percent,
        comparator=less_than_or_equal,
        rationale="High plasma protein binding causes variability and displacement interactions",
        severity=Severity.SEVERE,
        provenance=Provenance(
            source_type="pharmacokinetics",
            confidence=0.75,
            references=[
                "doi:10.1007/s00280-009-1199-8"
            ]
        )
    )


def aqueous_solubility_min(min_sol_ug_mL: float = 10.0) -> Constraint:
    """
    Minimum acceptable aqueous solubility (μg/mL, pH 7.4).

    Rationale:
        Solubility governs dissolution and absorption of oral drugs,
        and is essential for parenteral formulation.

        < 1 μg/mL: Practically insoluble — major formulation barrier
        1–10 μg/mL: Slightly soluble — formulation challenge
        > 10 μg/mL: Generally acceptable for early candidates
        > 100 μg/mL: Excellent

    Default (10 μg/mL) is appropriate for early-stage screening.
    For IV-only formulations, this constraint may be relaxed.

    References:
        Lipinski (2000) — Drug-like properties and solubility
    """
    return Constraint(
        name="aqueous_solubility",
        threshold=min_sol_ug_mL,
        comparator=greater_than_or_equal,
        rationale="Poor aqueous solubility limits absorption and complicates formulation",
        severity=Severity.SEVERE,
        provenance=Provenance(
            source_type="physicochemical_screening",
            confidence=0.80,
            references=[
                "doi:10.1002/jps.1190"
            ]
        )
    )


# ---------------------------------------------------------------------
# Convenience constraint bundles
# ---------------------------------------------------------------------

def core_safety_constraints() -> List[Constraint]:
    """
    Standard baseline safety constraint set.

    Intended for:
        - Early conceptual screening
        - Framework demonstrations
        - Conservative default reasoning

    This set should be tightened (not loosened) for
    population-specific contexts.

    Includes:
        - logP ≤ 4.0
        - hERG IC50 ≥ 10 μM
        - β₁/β₂ selectivity ≥ 100x
    """
    return [
        logP_max(),
        hERG_ic50_min(),
        beta1_over_beta2_selectivity_min(),
    ]


def lipinski_rule_of_five() -> List[Constraint]:
    """
    Lipinski's Rule of Five for oral drug-likeness.

    Constraints:
        - MW ≤ 500 Da
        - logP ≤ 5 (relaxed from our default 4.0)
        - HBD ≤ 5
        - HBA ≤ 10

    Note: CuraFrame defaults are more conservative than Ro5.
    Use this bundle when applying classic medicinal chemistry filters.
    """
    return [
        molecular_weight_range(min_mw=150.0, max_mw=500.0),
        logP_max(max_logP=5.0),
        hydrogen_bond_donors_max(max_hbd=5),
        hydrogen_bond_acceptors_max(max_hba=10),
    ]


def cns_drug_constraints() -> List[Constraint]:
    """
    Constraint set for CNS-active drugs.

    Stricter than general medicinal chemistry guidelines:
        - logP: 2.0-3.8
        - PSA: 40-80 Ų
        - MW: 150-450 Da

    Based on CNS MPO principles (Wager et al., 2010).

    Use for: Brain-penetrant therapeutics.
    """
    return [
        logP_range(min_logP=2.0, max_logP=3.8),
        cns_psa_range(min_psa=40.0, max_psa=80.0),
        molecular_weight_range(min_mw=150.0, max_mw=450.0),
        hydrogen_bond_donors_max(max_hbd=2),
        hydrogen_bond_acceptors_max(max_hba=7),
    ]


def cardiology_oriented_constraints() -> List[Constraint]:
    """
    Constraint set emphasizing cardiovascular safety.

    Builds on core safety constraints with:
        - Stricter hERG requirements
        - Molecular weight limits
        - β-adrenergic selectivity

    Use for: Cardiovascular therapeutics or drugs with cardiac risk.
    """
    return [
        logP_max(),
        hERG_ic50_min(min_ic50_uM=15.0),  # More conservative for cardiology
        beta1_over_beta2_selectivity_min(),
        molecular_weight_range(),
    ]


def cardiAnx_dual_domain_constraints() -> List[Constraint]:
    """
    Constraint set for CardiAnx-1 dual-domain concept.

    Combines:
        - CNS penetration (BBB crossing)
        - Cardiac safety (hERG, β-selectivity)
        - Serotonergic targeting (5-HT₁ₐ, avoid 5-HT₂ₐ)

    This represents the full design space defined in:
        Krüger & Feeney (2025) - CardiAnx-1 manuscript

    Physicochemical window:
        - logP: 2.5-3.8
        - PSA: <80 Ų
        - MW: 450-520 Da
        - HBD: ≤2, HBA: ≤7

    Target profile:
        - β₁ antagonism: high affinity (Kd ~1 nM)
        - 5-HT₁ₐ partial agonism: moderate (Kd ~10 nM)
        - β₂ avoidance: >100x selectivity
        - 5-HT₂ₐ, D₂ avoidance

    Safety:
        - hERG IC50 > 10 μM
    """
    return [
        # Physicochemical (BBB + cardiac distribution)
        logP_range(min_logP=2.5, max_logP=3.8),
        polar_surface_area_max(max_psa=80.0),
        molecular_weight_range(min_mw=450.0, max_mw=520.0),
        hydrogen_bond_donors_max(max_hbd=2),
        hydrogen_bond_acceptors_max(max_hba=7),

        # Cardiac safety
        hERG_ic50_min(min_ic50_uM=10.0),
        beta1_over_beta2_selectivity_min(min_selectivity=100.0),

        # Target profile
        serotonin_5ht1a_affinity_range(min_Kd_nM=5.0, max_Kd_nM=20.0),
        off_target_5ht2a_avoidance(max_affinity_nM=500.0),
        dopamine_d2_avoidance(max_affinity_nM=1000.0),

        # Pharmacokinetics
        plasma_half_life_range(min_t_half_hours=8.0, max_t_half_hours=16.0),
    ]


def oncology_constraints() -> List[Constraint]:
    """
    Constraint set for oncology (anti-cancer) drug candidates.

    Rationale:
        Oncology drugs operate under different safety trade-offs.
        Cytotoxicity in normal tissue is more acceptable than in
        other indications, but selectivity for cancer vs normal cells
        and avoidance of serious metabolic liabilities is still critical.

    Constraints:
        - logP: 1.0–5.0 (broader range for diverse targets)
        - MW: 150–600 Da (larger scaffolds common in targeted therapy)
        - hERG IC50 ≥ 10 μM (cardiac safety remains essential)
        - CYP3A4 IC50 ≥ 10 μM (DDI risk in polypharmacy patients)
        - Therapeutic index ≥ 2.0 (narrower window acceptable)
        - Protein binding ≤ 97% (free drug critical for efficacy)
        - Aqueous solubility ≥ 1 μg/mL (IV formulation may supplement)

    Use for: Small-molecule anti-cancer agents, kinase inhibitors.
    """
    return [
        # Physicochemical
        logP_range(min_logP=1.0, max_logP=5.0),
        molecular_weight_range(min_mw=150.0, max_mw=600.0),
        hydrogen_bond_donors_max(max_hbd=5),
        hydrogen_bond_acceptors_max(max_hba=10),

        # Cardiac safety
        hERG_ic50_min(min_ic50_uM=10.0),

        # Metabolic safety
        cyp3a4_inhibition_min(min_ic50_uM=10.0),

        # Efficacy/toxicity window
        therapeutic_index_min(min_ti=2.0),

        # Distribution
        protein_binding_max(max_ppb_percent=97.0),
        aqueous_solubility_min(min_sol_ug_mL=1.0),
    ]


def anti_infective_constraints() -> List[Constraint]:
    """
    Constraint set for anti-infective (antibacterial/antiviral) candidates.

    Rationale:
        Anti-infectives must penetrate bacterial membranes or viral
        envelopes while avoiding toxicity to host cells. Gram-negative
        coverage requires lower MW and moderate logP for outer membrane
        penetration. Solubility and low protein binding maximise free
        drug at the site of infection.

    Constraints:
        - logP: −1.0 to 3.0 (hydrophilic for Gram-negative penetration)
        - MW: 150–500 Da (outer membrane porin size limit)
        - HBD ≤ 5, HBA ≤ 10 (permeability)
        - hERG IC50 ≥ 10 μM (cardiac safety)
        - CYP3A4 IC50 ≥ 10 μM (DDI in co-infected patients)
        - Protein binding ≤ 80% (free drug drives antimicrobial activity)
        - Aqueous solubility ≥ 50 μg/mL (IV dosing requirements)
        - Oral bioavailability ≥ 30% (step-down oral therapy)

    Use for: Antibacterials, antifungals, antiparasitics.
    """
    return [
        # Physicochemical (Gram-negative penetration)
        logP_range(min_logP=-1.0, max_logP=3.0),
        molecular_weight_range(min_mw=150.0, max_mw=500.0),
        hydrogen_bond_donors_max(max_hbd=5),
        hydrogen_bond_acceptors_max(max_hba=10),

        # Cardiac safety
        hERG_ic50_min(min_ic50_uM=10.0),

        # Metabolic safety
        cyp3a4_inhibition_min(min_ic50_uM=10.0),

        # Distribution (free drug drives MIC)
        protein_binding_max(max_ppb_percent=80.0),
        aqueous_solubility_min(min_sol_ug_mL=50.0),

        # Oral step-down
        oral_bioavailability_min(min_F_percent=30.0),
    ]


def metabolic_disease_constraints() -> List[Constraint]:
    """
    Constraint set for metabolic disease (diabetes, obesity, dyslipidaemia)
    drug candidates.

    Rationale:
        Metabolic disease agents are taken chronically by large patient
        populations that often have polypharmacy. Long-term safety,
        metabolic stability, reliable oral bioavailability, and
        predictable pharmacokinetics are paramount.

    Constraints:
        - logP: 0.5–4.0 (moderate lipophilicity for oral absorption)
        - MW: 150–500 Da (drug-like for oral therapy)
        - HBD ≤ 5, HBA ≤ 10 (oral permeability)
        - hERG IC50 ≥ 10 μM (cardiac safety in metabolic syndrome)
        - CYP3A4 IC50 ≥ 10 μM (DDI — statins, antihypertensives common)
        - Plasma half-life: 8–24 h (once-daily dosing compliance)
        - Hepatic clearance ≤ 30 mL/min/kg (metabolic stability)
        - Oral bioavailability ≥ 40% (predictable chronic exposure)
        - Protein binding ≤ 95% (chronic dosing variability)
        - Aqueous solubility ≥ 10 μg/mL

    Use for: Anti-diabetics, GLP-1 analogues, SGLT2/DPP-4 inhibitors,
             statins, fibrates, anti-obesity agents.
    """
    return [
        # Physicochemical
        logP_range(min_logP=0.5, max_logP=4.0),
        molecular_weight_range(min_mw=150.0, max_mw=500.0),
        hydrogen_bond_donors_max(max_hbd=5),
        hydrogen_bond_acceptors_max(max_hba=10),

        # Cardiac safety (metabolic syndrome elevates CV risk)
        hERG_ic50_min(min_ic50_uM=10.0),

        # Metabolic safety (polypharmacy population)
        cyp3a4_inhibition_min(min_ic50_uM=10.0),
        hepatic_clearance_max(max_CL_mL_min_kg=30.0),

        # Pharmacokinetics (chronic dosing)
        plasma_half_life_range(min_t_half_hours=8.0, max_t_half_hours=24.0),
        oral_bioavailability_min(min_F_percent=40.0),

        # Distribution
        protein_binding_max(max_ppb_percent=95.0),
        aqueous_solubility_min(min_sol_ug_mL=10.0),
    ]
