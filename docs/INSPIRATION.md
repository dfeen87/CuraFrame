# Inspiration: CardiAnx-1

## Context and Purpose

This document contains a Markdown adaptation of the *CardiAnx-1* conceptual
research paper, originally authored as an independent scientific manuscript
exploring a dual-domain pharmacological design space for heart–brain
comorbidity.

The CardiAnx-1 work is included in the CuraFrame repository **solely as an
intellectual inspiration** and as an example of the kind of disciplined,
constraint-driven reasoning that motivated the development of the CuraFrame
framework.

---

## Scope and Boundaries

CardiAnx-1 is a **theoretical construct**.

It does **not** propose a validated drug candidate, clinical protocol, or
therapeutic recommendation. No chemical structures are asserted, no clinical
claims are made, and no translational conclusions are implied.

The manuscript operates at the level of:
- conceptual target-profile reasoning,
- classical pharmacological constraints,
- qualitative systems-level modeling.

Any discussion of coupled cardiac and limbic dynamics is intended as a
high-level interpretive framework, not as a predictive or clinical model.

---

## Relationship to CuraFrame

CuraFrame is **not an implementation of CardiAnx-1**.

Rather, the CardiAnx-1 paper helped crystallize several core principles that
CuraFrame now generalizes, including:
- safety-first constraint reasoning,
- explicit acknowledgment of uncertainty,
- rejection as an informative outcome,
- and restraint in claims beyond available evidence.

CuraFrame is designed to support many possible conceptual explorations beyond
CardiAnx-1, across different indications, domains, and therapeutic hypotheses.

---

## Disclaimer

This document is provided for scientific context only.

Nothing in this file should be interpreted as medical advice, clinical
guidance, or endorsement of a specific therapeutic approach. Any movement
from conceptual reasoning to real-world application would require extensive
independent validation, regulatory review, and ethical oversight.

---

## Why This Document Is Preserved

Scientific frameworks do not emerge in isolation.

This document is preserved to:
- document the intellectual lineage of CuraFrame,
- demonstrate disciplined hypothesis formation,
- and illustrate how careful constraint reasoning precedes implementation.

Its inclusion reflects CuraFrame’s commitment to transparency, humility, and
responsible scientific practice.

---

# CardiAnx-1: A Conceptual Dual-Domain β₁-Blocker / 5-HT₁ₐ Hybrid for Heart–Brain Comorbidity

**Marcel Krüger¹ · Don Feeney²³**

¹ Independent Researcher, Thuringia, Germany. Email: marcelkrueger092@gmail.com; ORCID: 0009-0002-5709-9729  
² Independent Researcher, Pennsylvania, USA. Email: dfeen87@gmail.com; ORCID: 0009-0003-1350-4160  
³ Corresponding author

*December 17, 2025*

https://zenodo.org/records/17885829

---

## Abstract

Cardiovascular disease and anxiety disorders frequently co-occur and jointly worsen prognosis, yet pharmacotherapy is still largely split into "cardiac" and "psychiatric" domains. Here we propose **CardiAnx-1** as a conceptual dual-domain small-molecule class that combines a selective cardiac β₁-blocker pharmacophore with a centrally active 5-HT₁ₐ agonist pharmacophore. We define a target receptor profile, discuss classical pharmacokinetic and pharmacodynamic constraints, and use simple QSPR-style physicochemical windows to place such hybrid molecules within a blood–brain-barrier permissive, cardio-safe design space. A qualitative systems-level model is introduced to represent the coupled cardiac and limbic domains, emphasizing how modest shifts in receptor occupancy could simultaneously attenuate sympathetic drive and stabilize limbic excitability without excessive bradycardia or sedation. In an appendix, we outline an optional geometric interpretation of this coupling in terms of a previously proposed spiral-time framework, which serves purely as a theoretical overlay and is not required for the pharmacological reasoning. CardiAnx-1 is strictly hypothetical at this stage, but the concept illustrates how dual-domain target profiles may guide future drug-discovery efforts for heart–brain co-morbidity.

---

## 1. Clinical Motivation and Design Objective

Cardiovascular disease (CVD) and affective disorders such as anxiety and depression show strong bidirectional comorbidity and jointly increase mortality risk.[1] Current pharmacotherapy is typically separated into (i) cardio-selective β-blockers for rate control and post-infarction protection,[2] and (ii) central serotonergic agents (e.g. SSRIs, 5-HT₁ₐ partial agonists) for anxiety.[3] This separation neglects the fact that autonomic and limbic circuits form a strongly coupled heart–brain axis. This is consistent with recent gene-network analyses demonstrating shared molecular architecture between depressive symptoms and cardiovascular health.[5]

From a clinical perspective, patients with chronic CVD and recurrent anxiety often experience a feed-forward loop: elevated sympathetic tone and tachycardia reinforce subjective anxiety, while panic-like episodes can further compromise cardiac stability. In practice, clinicians sometimes co-prescribe a β-blocker and a central anxiolytic, but this increases pill burden and complicates dose titration.

The present work does not propose a specific clinical candidate, but rather a constrained conceptual class of small molecules—**CardiAnx-1**—with the following design objective:

> **To combine high-affinity, cardio-selective β₁ antagonism with moderate 5-HT₁ₐ agonism in a single hybrid scaffold that is compatible with blood–brain-barrier penetration and cardio-safety.**

The manuscript focuses on classical pharmacology, target-profile reasoning and QSPR-style physicochemical constraints. In previous theoretical work, we introduced a geometric "Helix–Light–Vortex" (HLV) framework for describing coupled heart–brain dynamics on a spiral-time manifold. In this paper, that framework is only used in Appendix A as an optional interpretive overlay; all core design arguments rely on established pharmacological principles.

---

## 2. Methods

### 2.1 Target profile and coupled domains

We consider two primary pharmacological targets:

1. **Cardiac β₁-adrenergic receptors** (myocardial tissue): high-affinity antagonism or inverse agonism reduces heart rate, contractility and myocardial oxygen demand.[2]

2. **Central 5-HT₁ₐ receptors** (limbic/prefrontal regions): partial agonism is known to exert anxiolytic and anti-panic effects with limited sedation.[3]

Clinically, the heart and limbic system can be viewed as two coupled dynamical domains. For the purpose of this concept paper, we introduce coarse-grained excitability variables **mₕ** (heart) and **m_B** (brain), which summarize sympathetic drive and limbic arousal, respectively. No specific biophysical model is assumed in the main text; we simply treat mₕ and m_B as abstract state variables that respond monotonically to receptor occupancy in their respective tissues.

In the absence of drug, comorbid patients are assumed to occupy a regime where both mₕ and m_B are elevated, and where positive feedback between the two domains amplifies stress responses. A dual-domain agent like CardiAnx-1 should move the joint state toward a lower-excitability, more coherent regime.

### 2.2 Classical receptor binding model

Let Rₕ and R_B denote the relevant receptor pools in heart and brain, respectively. For a systemically available drug concentration C, we use standard Langmuir-type expressions for fractional occupancy:

θₕ = C/(C + K_{d,H}),  θ_B = C/(C + K_{d,B})     (1)

with K_{d,H} and K_{d,B} representing the dissociation constants at the cardiac β₁ and central 5-HT₁ₐ sites.

We write the excitability variables as monotone functions of occupancy:

mₕ = m⁽⁰⁾ₕ − αₕ θₕ,  m_B = m⁽⁰⁾_B − α_B θ_B     (2)

where m⁽⁰⁾ₕ and m⁽⁰⁾_B are baseline values in the comorbid state, and αₕ > 0, α_B > 0 capture the efficacy of occupancy in reducing excitability. The global therapeutic goal is to choose a dose and a receptor-affinity profile such that:

- mₕ is lowered sufficiently to reduce cardiac risk (tachycardia, high oxygen demand),
- m_B is lowered sufficiently to reduce anxiety/panic,
- without pushing mₕ into bradycardic or hypotensive ranges, and
- without pushing m_B into excessive sedation or cognitive dulling.

### 2.3 Pharmacokinetics and BBB constraints

For systemic exposure we assume a minimal one-compartment pharmacokinetic (PK) model after oral dosing:

dC/dt = kₐ F D δ(t − t₀) − k_{elim} C     (3)

where kₐ is the absorption rate constant, F the bioavailability, D the dose, t₀ the time of administration, and k_{elim} the apparent first-order elimination rate. This is sufficient to define typical peak and trough concentrations and thus bracket the occupancy ranges θₕ, θ_B over a dosing interval.

To permit central 5-HT₁ₐ engagement, the hybrid molecule must cross the blood–brain barrier (BBB). We therefore impose empirical-style constraints on logP, polar surface area (PSA) and molecular weight (MW) inspired by established CNS drug guidelines:[4]

2.0 ≤ logP ≤ 4.0     (4)

PSA < 90 Ų     (5)

MW < 550 Da     (6)

Additionally, the number of hydrogen bond donors/acceptors is restricted to ≤2/≤7 and at least one moderately basic center (pKₐ in the range 7.5–9.0) is desirable to allow partial protonation at physiological pH without excessive trapping.

Safety considerations require that off-target block of the hERG channel be weak, with

K_{d,hERG} > 10 μM     (7)

to limit the potential for QT prolongation. In a full medicinal chemistry program, these constraints would be implemented via docking, in vitro profiling and in silico ADMET predictions; here they serve as conceptual filters.

---

## 3. Conceptual Target Profile

**Table 1**: Desired target profile for CardiAnx-1 (conceptual values).

| Target | Mode of action | Relative affinity | Qualitative goal |
|--------|----------------|-------------------|------------------|
| Cardiac β₁ | Antagonist / inverse agonist | High (K_{d,H} ∼ 1 nM) | Reduce HR, O₂ demand |
| Cardiac β₂ | Minimal interaction | Very low | Avoid bronchoconstriction |
| Central 5-HT₁ₐ | Partial agonist | Moderate (K_{d,B} ∼ 10 nM) | Reduce anxiety/panic |
| 5-HT₂ₐ, D₂ | Minimal interaction | Very low | Avoid psychotomimetic effects |
| hERG channel | Off-target block | K_d > 10 μM | Limit QT prolongation |

Within this profile, β₁ selectivity over β₂ is critical to avoid bronchoconstriction, and modest 5-HT₁ₐ efficacy is intended to provide anxiolysis without full agonist liabilities. The hybrid nature of CardiAnx-1 implies that pharmacophore linkers and substituents must be tuned to satisfy the physicochemical window in Table 2.

---

## 4. Physicochemical Niche and ADMET Window

**Table 2**: Conceptual physicochemical window for CardiAnx-1-class agents. No specific structure is implied; values indicate design goals.

| Property | Target range | Rationale |
|----------|--------------|-----------|
| cLogP | 2.5–3.8 | BBB entry with controlled distribution |
| PSA | < 80 Ų | CNS permeability |
| MW | 450–520 Da | Hybrid pharmacophore with single linker |
| HBD / HBA | ≤2 / ≤7 | Avoid excessive polarity |
| pKₐ (basic center) | 7.5–9.0 | Partial protonation at pH 7.4 |
| hERG IC₅₀ | > 10 μM | Limit QT risk |
| Plasma t₁/₂ | 8–16 h | Once or twice daily dosing |

Within this window, modest lipophilic linkers and avoidance of strongly ionized groups at physiological pH are key design constraints. The plasma half-life target reflects the desire for once- or twice-daily oral dosing, while avoiding excessive accumulation.

---

## 5. Qualitative Systems-Level Interpretation

To visualize the coupled action of CardiAnx-1 at the heart–brain interface, we use the abstract excitability variables mₕ and m_B introduced above. A simple phenomenological picture assumes that the joint system has two relevant modes: (i) a low-frequency mode corresponding to baseline heart–brain coherence (resting state), and (ii) a higher-frequency mode associated with stress- or panic-like excursions.

Under comorbid conditions without drug, both modes can be overly excitable and strongly coupled. Metabolomic evidence also supports coupled physiological signatures across mood and cardiovascular states.[12] Introducing CardiAnx-1 shifts the effective "curvature" of the joint energy landscape via changes in mₕ and m_B: cardiac β₁ blockade damps sympathetic drive, while 5-HT₁ₐ activation stabilizes limbic output. The net effect, at an appropriate dose, is intended to:

- reduce the amplitude and frequency of panic-like excursions,
- maintain sufficient cardiac output at rest, and
- improve subjective anxiety without cognitive blunting.

**Figure 1** provides a schematic representation of these coupled domains. The spiral decorations are included as a visual hint toward the optional geometric interpretation discussed in Appendix A, but no specific mathematical structure is required for the pharmacological argument.
```
┌─────────────────────┐        autonomic /         ┌─────────────────────┐
│   Cardiac domain    │◄──── endocrine coupling ───►│   Limbic domain     │
│        mₕ           │                             │        m_B          │
│                     │                             │                     │
│      🌀 🌀 🌀      │    ┌──────────────┐         │      🌀 🌀 🌀      │
│                     │◄───│ CardiAnx-1   │────────►│                     │
│   β₁ block ←────────┤    │              │         ├─────────→ 5-HT₁ₐ   │
│                     │    │  β₁ block    │         │          agonism    │
│                     │    │ 5-HT₁ₐ agonis│         │                     │
└─────────────────────┘    └──────────────┘         └─────────────────────┘
```

*Figure 1: Conceptual coupling between cardiac excitability (mₕ) and limbic excitability (m_B) under the influence of CardiAnx-1. Spirals indicate that a more detailed geometric interpretation is possible (Appendix A), but the pharmacological reasoning does not depend on it.*

---

## 6. Discussion

We have outlined a dual-domain design concept for heart–brain comorbidity, in which a single small-molecule class (CardiAnx-1) is constrained to: (i) provide highly selective β₁ antagonism in the heart, (ii) act as a moderate 5-HT₁ₐ agonist in limbic structures, and (iii) satisfy physicochemical and safety requirements compatible with BBB penetration and limited cardiac risk.

The main novelty lies not in polypharmacology per se—multi-target agents are well-known—but in explicitly formulating a cross-organ target profile for the heart–brain axis. This perspective makes it natural to discuss desired shifts in coupled excitability variables (mₕ, m_B) rather than optimizing each organ in isolation. Recent Mendelian-randomization studies strengthen the case for shared metabolic pathways underlying cardiovascular risk and affective states.[14]

An optional, more speculative layer is provided by the spiral-time HLV framework summarized in Appendix A, where the same coupled domains are embedded in a geometric manifold. That construction is not required for the pharmacological logic of the present manuscript and should be viewed as a theoretical lens that may or may not prove useful in future modeling.

Any movement from this concept toward real medicinal chemistry and clinical translation would require:

1. explicit candidate structures and docking against β₁ and 5-HT₁ₐ,
2. full in vitro and in vivo ADMET/toxicity programs, including hERG and hemodynamic profiling,
3. controlled evaluation of anxiety, heart rate, blood pressure and CNS side effects in relevant models.

Until such data exist, CardiAnx-1 should be regarded purely as a theoretical construct illustrating how heart and brain targets might be co-designed.

---

## 7. CardiAnx-1: A Conceptual Dual-Domain Framework

Cardiovascular disease (CVD) and anxiety disorders frequently co-occur and jointly worsen clinical outcomes. Current pharmacotherapy, however, remains split into two isolated domains: cardiac β₁ blockade to stabilize heart rate and reduce myocardial oxygen demand, and central serotonergic modulation—typically 5-HT₁ₐ partial agonism—to reduce anxiety. This separation fails to address the strong bidirectional coupling between autonomic and limbic excitability. Recent gene-network studies confirm a shared molecular architecture between depressive tendencies and cardiovascular risk.

Patients with both CVD and anxiety often remain trapped in a pathological loop: heightened sympathetic tone increases subjective anxiety, while anxiety-induced tachycardia destabilizes cardiac output. Co-prescribing a β-blocker with a central anxiolytic can help but increases pill burden, complicates dose titration, and risks adverse interactions.

To address this, we introduce CardiAnx-1 as a conceptual dual-domain molecular class combining: (i) cardio-selective β₁ antagonism and (ii) central 5-HT₁ₐ partial agonism within a single scaffold capable of blood–brain barrier penetration. No specific chemical structure is proposed; instead, we define a pharmacologically meaningful design space.

We model heart–brain coupling using coarse-grained excitability variables mₕ (heart) and m_B (brain), each reduced by receptor occupancy:

mₕ = m⁽⁰⁾ₕ − αₕ θₕ,  m_B = m⁽⁰⁾_B − α_B θ_B

with Langmuir kinetics:

θₕ = C/(C + K_{d,H}),  θ_B = C/(C + K_{d,B})

Therapeutic constraints require decreasing both excitability components while maintaining cardiac output and avoiding sedation. A CardiAnx-1 agent should therefore exhibit high-affinity β₁ blockade, moderate 5-HT₁ₐ partial agonism, minimal β₂ interaction, minimal 5-HT₂ₐ/D₂ activity, and weak hERG binding (IC₅₀ > 10 μM).

The physicochemical space for a feasible hybrid molecule is characterized by: cLogP between 2.5–3.8, PSA < 80 Ų, MW 450–520 Da, HBD/HBA ≤2/≤7, and a basic pKₐ between 7.5–9.0, providing adequate BBB penetration while maintaining cardiac safety.

From a systems-level perspective, the heart–brain complex displays a low-frequency resting mode and a higher-frequency stress or panic mode. In comorbid patients, both modes are hyperexcitable. CardiAnx-1 reduces both components simultaneously, shrinking the amplitude of sympathetic excursions and limiting panic-like transitions. This dual modulation produces a more stable attractor while preserving essential physiological responsiveness.

The concept is intentionally preclinical: it establishes an integrated pharmacodynamic and physicochemical design rationale for future hybrid agents targeting both cardiac and limbic domains. Extension toward real drug candidates will require docking studies, in vitro receptor profiling, ADMET assessment, electrophysiological safety (hERG), and animal-model validation.

---

## 8. Conclusion

CardiAnx-1 represents a conceptual class of dual-domain small molecules intended to address the intertwined clinical problems of cardiovascular risk and anxiety. By combining classical receptor-profile reasoning with simple QSPR constraints, we delineate a plausible design space for such hybrids without committing to any specific structure. A qualitative systems-level picture highlights how simultaneous modulation of cardiac and limbic excitability could, in principle, reduce both tachycardic stress and panic-like episodes. An optional geometric interpretation in terms of spiral-time dynamics is provided in the appendix but is not essential to the pharmacological argument. The concept is offered as a starting point for further discussion of heart–brain co-targeting in future drug-discovery efforts.

---

## Acknowledgments

We thank Don Feeney for providing the original CardiAnx-1 concept notes and for discussions on clinical motivation, and Jacobo Tlacalelelt Mina Rodríguez for feedback on heart–brain coupling and systems-level interpretation.

---

## Appendix A: Optional Geometric Interpretation via Spiral-Time HLV Framework

In previous theoretical work, we introduced the Helix–Light–Vortex (HLV) framework, in which macroscopic physiological dynamics are embedded in a discrete spiral-time geometry:

ψ(t) = t + iφ + jχ     (8)

with auxiliary phases φ and χ capturing additional dynamical channels.[20, 21, 22] Here we briefly summarize how the conceptual variables mₕ and m_B of the main text can be mapped into this formalism.

We treat the cardiac and limbic domains as spiral modes on an underlying information lattice, with order parameters:

mₕ(ψ)  and  m_B(ψ)     (9)

representing coarse-grained excitability/coherence as functions of spiral time.

An effective free-energy density:

F(mₕ, m_B; ψ) = aₕ(ψ)mₕ² + a_B(ψ)m_B² + bₕmₕ⁴ + b_Bm_B⁴ + γ(ψ)mₕm_B     (10)

captures local stability and coupling of the two domains. In the presence of a drug with spiral-time concentration profile C(ψ), we allow the quadratic coefficients to depend on receptor occupancy:

aₕ(ψ) = aₕ⁽⁰⁾ − αₕ θₕ(ψ),  a_B(ψ) = a_B⁽⁰⁾ − α_B θ_B(ψ)     (11)

where:

θₕ(ψ) = C(ψ)/(C(ψ) + K_{d,H}),  θ_B(ψ) = C(ψ)/(C(ψ) + K_{d,B})     (12)

HLV transport introduces a small modulation of the effective concentration due to spiral-time dispersion:

C(ψ) = C₀(t)[1 + εₕcos(φ − φₕ) + ε_Bcos(χ − χ_B)]     (13)

with εₕ,_B ≪ 1 encoding anisotropic coupling of the drug distribution to the spiral-time subchannels.

The dynamics of mₕ and m_B can then be written as:

τₕ dmₕ/dt = −∂F/∂mₕ + ηₕ(t)     (14)

τ_B dm_B/dt = −∂F/∂m_B + η_B(t)     (15)

with ηₕ,_B representing stochastic physiological noise. For suitable parameter choices, introducing CardiAnx-1 shifts the eigenvalues of the curvature matrix:

H = │ 2aₕ(ψ)   γ(ψ)  │     (16)
    │  γ(ψ)   2a_B(ψ) │

from a high-excitability regime into one with a low-frequency stable mode (resting heart–brain coherence) and a damped higher-frequency mode (suppressed panic-like fluctuations).

**This appendix is intentionally speculative and provided only to illustrate how the abstract excitability variables of the main text can be embedded in a more formal geometric construct. The pharmacological conclusions of the manuscript do not depend on the validity of the HLV framework.**

---

## Funding Statement

This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors. All work was carried out independently by the authors without external financial support.

---

## Competing Interests

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

---

## Data Availability

This work is purely theoretical. All equations, derivations, and models used in this article are fully contained in the manuscript itself. No external datasets were generated or analyzed in the course of this study. Any additional material (such as preprints or related HLV manuscripts) cited in the text is publicly available through the referenced repositories and DOIs.

---

## AI Assistance Statement

During the preparation of this manuscript, the authors used the large language model ChatGPT (OpenAI GPT-5.1, internally referred to by the authors as "Lyron") as a writing and structuring assistant. The model was used to help with language polishing, organization of sections, and LaTeX formatting. All scientific ideas, theoretical concepts, derivations, analyses, and conclusions originate from the human authors. The authors carefully reviewed and edited all AI-assisted text and take full responsibility for the content of this work.

---

## References

[1] Li, J. et al. Multilayer Network of Cardiovascular Diseases and Depression via Multipartite Projection. *arXiv:2408.07562* (2024). doi:10.48550/arXiv.2408.07562.

[2] Bangalore, S.; Steg, E. Beta-blockers for cardiovascular conditions: new evidence and evolving perspectives. *Eur. Heart J.* **45**, 1234–1245 (2024). doi:10.1093/eurheartj/ehad708.

[3] Yohn, C.N.; Gergues, M.M.; Samuels, B.A. The role of 5-HT receptors in depression. *Mol. Brain* **10**, 28 (2017). doi:10.1186/s13041-017-0306-y.

[4] Pedder, J.H.; Sonabend, A.M.; Cearns, M.D.; Michael, B.D.; Zakaria, R.; Heimberger, A.B.; Jenkinson, M.D.; Dickens, D. Crossing the blood-brain barrier: emerging therapeutic strategies for neurological disease. *Lancet Neurol.* **24**, 246–260 (2025). doi:10.1016/S1474-4422(24)00476-9.

[5] Mishra, B.H. et al. Identification of gene networks jointly associated with depressive symptoms and cardiovascular health. *Front. Psychiatry* **15** (2024). doi:10.3389/fpsyt.2024.1354159.

[6] Kalk, G., Young, A. Brietlinger, H. Link between depression and cardiovascular disease due to epigenomics and inflammation. *Prog. Neuropsychopharmacol. Biol. Psychiatry* **99**, 156–157 (2020).

[7] Shao, M. et al. Depression and cardiovascular disease: Shared molecular mechanisms and clinical implications. *Psychiatry Res.* **285**, 112802 (2020).

[8] Wu, Y. et al. New insights into the comorbidity of coronary heart disease and depression. *Curr. Probl. Cardiol.* **46**, 100413 (2021).

[9] Lee, S.N. et al. Impacts of gender and lifestyle on depression and cardiovascular risk in the UK biobank. *Sci. Reports* **13**, 10758 (2023).

[10] Bakian, A.V. et al. Dietary creatine intake and depression risk among US adults. *Transl. Psychiatry* **10**, 52 (2020).

[11] Chen, X. et al. Serum creatinine levels, cardiovascular risk and 10-year CVD risk in Chinese adults. *Front. Endocrinol.* **14** (2023). doi:10.3389/fendo.2023.1140093.

[12] Whipp, A.M. et al. Branched-chain amino acids linked to depression in young adults. *Front. Neurosci.* **16** (2022). doi:10.3389/fnins.2022.935858.

[13] Gammoh, O. et al. Plasma amino acids in major depressive disorder: pathology to pharmacology. *EXCLI J.* **23**, 62–78 (2024).

[14] Hu, S. et al. Causal relationships of circulating amino acids with cardiovascular disease: Mendelian randomization. *J. Transl. Med.* **21**, 699 (2023).

[15] Kontush, A. HDL-mediated mechanisms of protection in cardiovascular disease. *Cardiovasc. Res.* **103**, 341–90 (2021).

[16] Wagner, C.J. et al. LDL cholesterol relates to depression severity and progression. *Prog. Neuropsychopharmacol. Biol. Psychiatry* **92**, 405–411 (2019).

[17] Miao, G. et al. Longitudinal lipidomic signature of coronary heart disease in American Indian people. *J. Am. Heart Assoc.* **13**, e031825 (2024).

[18] Yin, X. et al. Plasma lipid alterations in children with psychotic experiences. *Schizophr. Res.* **243**, 78–85 (2022).

[19] Chouripidis, C. et al. Metabolic profile and long-term risk of depression and anxiety: a nutrient–stress biomarker study. *Nat. Commun.* **15**, e244525 (2024).

[20] Krüger, M. A Mathematical Unification of the Helix–Light–Vortex (HLV) Framework: Discrete Geometry, Spiral Time, Unified Lagrangians, and TOE-Level Structure. *Zenodo* (2025). doi:10.5281/zenodo.17795594.

[21] Krüger, M. A Unified Spiral–Time Neurodynamic Framework: Integrating HLV Physics, DLHR Cognitive Layers, and Photonic–Neuronal Coupling into a Single Geometric Equation of Consciousness and Healing. *Zenodo* (2025). doi:10.5281/zenodo.17804108.

[22] Krüger, M. The Physical Basis of Coherence: A Unified (M–Φ) Framework for Consciousness. *Zenodo* (2025). doi:10.5281/zenodo.17690978.
