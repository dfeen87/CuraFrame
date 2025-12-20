"""
CuraFrame Console — Streamlit Application

A transparent constraint evaluation interface.

This application:
- Evaluates candidates against safety/design constraints
- Displays constraint violations with full context
- Exports constraint metadata for reproducibility

This application does NOT:
- Generate molecules
- Optimize properties
- Make clinical recommendations
- Replace medicinal chemistry expertise
"""

import json
from typing import Dict, Any
import streamlit as st

from cura_frame import (
    CuraFrame,
    Candidate,
    EvaluationStatus,
    Severity,
)
from cura_frame.constraints_library import (
    core_safety_constraints,
    lipinski_rule_of_five,
    cns_drug_constraints,
    cardiology_oriented_constraints,
    cardiAnx_dual_domain_constraints,
)


# -----------------------------
# Configuration
# -----------------------------

st.set_page_config(
    page_title="CuraFrame Console",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "CuraFrame: Constraint-driven therapeutic design reasoning"
    }
)

# Constraint bundle registry
BUNDLES = {
    "Core Safety": {
        "fn": core_safety_constraints,
        "description": "Baseline safety: logP, hERG, β-selectivity",
        "targets": "Early-stage screening, general drug-likeness"
    },
    "Lipinski Ro5": {
        "fn": lipinski_rule_of_five,
        "description": "Classic Rule of Five for oral bioavailability",
        "targets": "Oral drug candidates"
    },
    "CNS Constraints": {
        "fn": cns_drug_constraints,
        "description": "BBB penetration + CNS MPO principles",
        "targets": "Brain-penetrant therapeutics"
    },
    "Cardiology-Oriented": {
        "fn": cardiology_oriented_constraints,
        "description": "Cardiovascular safety emphasis",
        "targets": "Cardiac drugs or compounds with CV risk"
    },
    "CardiAnx Dual-Domain": {
        "fn": cardiAnx_dual_domain_constraints,
        "description": "β₁-blocker / 5-HT₁ₐ hybrid design space (Krüger & Feeney, 2025)",
        "targets": "Heart-brain comorbidity agents"
    },
}

# Population modifiers (examples)
POPULATION_MODIFIERS = {
    "elderly": {
        "hERG_IC50": lambda c: c.threshold * 1.5,
        "description": "More conservative hERG threshold (QT risk increases with age)"
    },
    "asthmatic": {
        "beta1_selectivity": lambda c: c.threshold * 2.0,
        "description": "Requires 200x β₁/β₂ selectivity (bronchoconstriction risk)"
    },
    "pediatric": {
        "hERG_IC50": lambda c: c.threshold * 1.3,
        "molecular_weight": lambda c: (c.threshold[0], c.threshold[1] * 0.9),
        "description": "Conservative safety margins for children"
    }
}


# -----------------------------
# Header
# -----------------------------

st.title("🧬 CuraFrame — Constraint Evaluation Console")
st.caption(
    "Constraint-driven reasoning only. "
    "**No generation. No optimization. No clinical decision support.**"
)

st.markdown("---")


# -----------------------------
# Sidebar: Configuration
# -----------------------------

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Bundle selection
    bundle_name = st.selectbox(
        "Constraint Bundle",
        list(BUNDLES.keys()),
        help="Select a predefined constraint set"
    )
    
    # Show bundle description
    bundle_info = BUNDLES[bundle_name]
    st.info(
        f"**Description:** {bundle_info['description']}\n\n"
        f"**Use for:** {bundle_info['targets']}"
    )
    
    st.markdown("---")
    
    # Evaluation mode
    st.subheader("Evaluation Mode")
    strict = st.toggle(
        "Strict mode",
        value=True,
        help="If enabled, missing properties → INDETERMINATE. "
             "If disabled, missing properties are skipped with warnings."
    )
    
    st.markdown("---")
    
    # Population stratification
    st.subheader("Population Context")
    
    use_population = st.checkbox("Apply population-specific modifiers")
    
    if use_population:
        population = st.selectbox(
            "Population",
            [""] + list(POPULATION_MODIFIERS.keys()),
            help="Apply constraint adjustments for specific patient populations"
        )
        
        if population and population in POPULATION_MODIFIERS:
            st.caption(f"ℹ️ {POPULATION_MODIFIERS[population]['description']}")
    else:
        population = None
    
    st.markdown("---")
    
    # File upload
    st.subheader("📄 Upload Candidate")
    uploaded = st.file_uploader(
        "Upload JSON file",
        type=["json"],
        help="Upload a candidate definition in JSON format"
    )


# -----------------------------
# Example candidates
# -----------------------------

EXAMPLES = {
    "Safe (passes core safety)": {
        "name": "safe_example",
        "properties": {
            "logP": 3.0,
            "hERG_IC50": 20.0,
            "beta1_selectivity": 150.0
        },
        "provenance": "example"
    },
    "Unsafe (hERG violation)": {
        "name": "unsafe_hERG",
        "properties": {
            "logP": 3.0,
            "hERG_IC50": 5.0,  # CRITICAL violation
            "beta1_selectivity": 150.0
        },
        "provenance": "example"
    },
    "CardiAnx-1 Template": {
        "name": "CardiAnx_template",
        "properties": {
            "logP": 3.2,
            "polar_surface_area": 75.0,
            "molecular_weight": 485.0,
            "hydrogen_bond_donors": 2,
            "hydrogen_bond_acceptors": 6,
            "hERG_IC50": 15.0,
            "beta1_selectivity": 170.0,
            "Kd_5HT1A": 12.0,
            "Kd_5HT2A": 650.0,
            "Kd_D2": 1200.0,
            "plasma_half_life": 12.0
        },
        "provenance": "CardiAnx-1_design_space"
    }
}


# -----------------------------
# Main interface: Input
# -----------------------------

st.header("📝 Candidate Definition")

col_example, col_input = st.columns([1, 3])

with col_example:
    st.subheader("Examples")
    example_choice = st.radio(
        "Load example",
        list(EXAMPLES.keys()),
        label_visibility="collapsed"
    )
    
    if st.button("Load Example"):
        st.session_state['candidate_json'] = json.dumps(
            EXAMPLES[example_choice],
            indent=2
        )

with col_input:
    # Check if uploaded file exists
    if uploaded is not None:
        try:
            candidate_text = uploaded.read().decode("utf-8")
            st.success(f"Loaded: {uploaded.name}")
        except Exception as e:
            st.error(f"Could not read uploaded file: {e}")
            candidate_text = st.session_state.get(
                'candidate_json',
                json.dumps(EXAMPLES["Safe (passes core safety)"], indent=2)
            )
    else:
        candidate_text = st.session_state.get(
            'candidate_json',
            json.dumps(EXAMPLES["Safe (passes core safety)"], indent=2)
        )
    
    candidate_text = st.text_area(
        "Candidate JSON",
        value=candidate_text,
        height=300,
        help="Define candidate properties in JSON format"
    )
    
    # Save to session state
    st.session_state['candidate_json'] = candidate_text


# -----------------------------
# Evaluation
# -----------------------------

st.markdown("---")

col_button, col_info = st.columns([1, 3])

with col_button:
    evaluate_button = st.button(
        "🔍 Run Evaluation",
        type="primary",
        use_container_width=True
    )

with col_info:
    st.caption(
        "Evaluation checks all constraints in selected bundle. "
        "Results are non-clinical and hypothetical."
    )


# -----------------------------
# Results display
# -----------------------------

if evaluate_button:
    try:
        # Parse candidate JSON
        raw = json.loads(candidate_text)
        cand = Candidate(
            name=raw.get("name", "unnamed"),
            properties=raw.get("properties", {}),
            provenance=raw.get("provenance")
        )
        
        # Build framework
        constraints = bundle_info["fn"]()
        cura = CuraFrame(constraints, name=f"CuraFrame::{bundle_name}")
        
        # Register population modifiers
        if use_population and population and population in POPULATION_MODIFIERS:
            pop_mods = {
                k: v for k, v in POPULATION_MODIFIERS[population].items()
                if k != "description"
            }
            cura.add_population(population, pop_mods)
        
        # Evaluate
        pop_arg = population if use_population else None
        result = cura.evaluate(cand, population=pop_arg, strict=strict)
        
        # Display results
        st.markdown("---")
        st.header("📊 Evaluation Results")
        
        # Status banner
        status_color = {
            EvaluationStatus.ACCEPTED: "success",
            EvaluationStatus.REJECTED: "error",
            EvaluationStatus.INDETERMINATE: "warning"
        }
        
        status_icon = {
            EvaluationStatus.ACCEPTED: "✅",
            EvaluationStatus.REJECTED: "❌",
            EvaluationStatus.INDETERMINATE: "⚠️"
        }
        
        st.markdown(
            f"### {status_icon[result.status]} Status: "
            f"`{result.status.value.upper()}`"
        )
        
        # Summary
        col_summary, col_export = st.columns([2, 1])
        
        with col_summary:
            st.subheader("Summary")
            st.code(result.summary(), language="text")
        
        with col_export:
            st.subheader("Export")
            
            # Export results as JSON
            export_data = {
                "candidate": {
                    "name": cand.name,
                    "properties": cand.properties,
                    "provenance": cand.provenance
                },
                "evaluation": {
                    "status": result.status.value,
                    "violations": [
                        {
                            "constraint": v.constraint,
                            "observed": str(v.observed),
                            "threshold": str(v.threshold),
                            "severity": v.severity.value,
                            "rationale": v.rationale
                        }
                        for v in result.violations
                    ],
                    "warnings": result.warnings,
                    "notes": result.notes
                },
                "configuration": {
                    "bundle": bundle_name,
                    "population": pop_arg,
                    "strict": strict
                }
            }
            
            st.download_button(
                "Download Results (JSON)",
                data=json.dumps(export_data, indent=2),
                file_name=f"curaframe_result_{cand.name}.json",
                mime="application/json",
                use_container_width=True
            )
            
            # Export constraint metadata
            st.download_button(
                "Download Constraints (JSON)",
                data=json.dumps(cura.export_constraints(), indent=2),
                file_name=f"curaframe_constraints_{bundle_name}.json",
                mime="application/json",
                use_container_width=True
            )
        
        # Detailed violation breakdown
        if result.violations:
            st.markdown("---")
            st.subheader("🔴 Constraint Violations")
            
            for i, violation in enumerate(result.violations, 1):
                severity_color = {
                    Severity.CRITICAL: "🔴",
                    Severity.SEVERE: "🟠",
                    Severity.WARNING: "🟡"
                }
                
                with st.expander(
                    f"{severity_color[violation.severity]} "
                    f"**{violation.constraint}** — "
                    f"{violation.severity.value.upper()}",
                    expanded=(i <= 3)  # Auto-expand first 3
                ):
                    col_v1, col_v2 = st.columns(2)
                    
                    with col_v1:
                        st.metric("Observed", f"{violation.observed}")
                        st.metric("Threshold", f"{violation.threshold}")
                    
                    with col_v2:
                        st.metric("Severity", violation.severity.value.upper())
                        st.metric("Confidence", f"{violation.confidence:.2f}")
                    
                    st.markdown(f"**Rationale:** {violation.rationale}")
        
        # Warnings
        if result.warnings:
            st.markdown("---")
            st.subheader("⚠️ Warnings")
            for warning in result.warnings:
                st.warning(warning)
        
        # Constraint details
        with st.expander("📋 View All Constraints in Bundle"):
            st.json(cura.export_constraints())
        
    except json.JSONDecodeError as e:
        st.error(f"❌ **Invalid JSON:** {e}")
        st.code(candidate_text, language="json")
    
    except Exception as e:
        st.error(f"❌ **Evaluation failed:** {e}")
        st.exception(e)


# -----------------------------
# Footer: Philosophy & Usage
# -----------------------------

st.markdown("---")

col_phil, col_usage = st.columns(2)

with col_phil:
    st.subheader("🧭 CuraFrame Philosophy")
    st.markdown(
        """
        CuraFrame exists to support **safe, disciplined, systems-level reasoning in medicine**.
        
        **What it is:**
        - A constraint-driven scientific framework
        - A tool for evaluating safety boundaries
        - A system for transparent, auditable reasoning
        
        **What it is NOT:**
        - A drug discovery engine
        - A molecule generator
        - A clinical recommendation system
        - A replacement for medicinal chemistry expertise
        
        > *"This cannot be done safely."*  
        > That answer is considered **success**.
        """
    )

with col_usage:
    st.subheader("📖 How to Use")
    st.markdown(
        """
        **1. Select a constraint bundle** (sidebar)
        - Choose based on therapeutic area
        - Each bundle has different safety/design criteria
        
        **2. Define your candidate** (main panel)
        - Enter properties as JSON
        - Use examples as templates
        - Upload from file if available
        
        **3. (Optional) Apply population context**
        - Select patient population if applicable
        - Constraints auto-adjust for vulnerable groups
        
        **4. Evaluate**
        - Click "Run Evaluation"
        - Review violations and warnings
        - Export results for documentation
        
        **Outcome Meanings:**
        - ✅ **ACCEPTED:** All constraints satisfied (hypothetical, non-clinical)
        - ❌ **REJECTED:** One or more critical constraints violated
        - ⚠️ **INDETERMINATE:** Insufficient data or evaluation error
        """
    )

# Credits
st.markdown("---")
st.caption(
    "CuraFrame Console v1.0 | "
    "Inspired by Krüger & Feeney (2025) — CardiAnx-1 Dual-Domain Concept | "
    "See `PHILOSOPHY.md` for framework principles"
)
```

## Key Enhancements

### 1. **Better UX**
- Example candidates (safe, unsafe, CardiAnx-1 template)
- Load examples with one click
- Visual status indicators (✅❌⚠️)
- Expandable violation details
- Downloadable results and constraints

### 2. **Population Modifiers**
- Pre-defined population adjustments (elderly, asthmatic, pediatric)
- Descriptions explain why modifiers are applied
- Optional toggle to enable/disable

### 3. **Enhanced Results Display**
- Color-coded status banners
- Detailed violation breakdowns with metrics
- Severity icons (🔴🟠🟡)
- Warnings section
- Full constraint metadata viewer

### 4. **Export Functionality**
- Download evaluation results as JSON
- Download constraint definitions for reproducibility
- Timestamped filenames

### 5. **Educational Content**
- Philosophy panel explains CuraFrame principles
- Usage guide for new users
- Bundle descriptions with use cases
- Inline help text throughout

### 6. **Better Error Handling**
- Graceful JSON parsing errors
- File upload error handling
- Exception display for debugging

### 7. **Session State**
- Preserves candidate JSON between runs
- Allows iterative refinement

## Usage Flow
```
1. User selects "CardiAnx Dual-Domain" bundle
2. Clicks "Load Example" → "CardiAnx-1 Template"
3. Optionally selects "asthmatic" population
4. Clicks "Run Evaluation"
5. Views violations with full context
6. Downloads results for documentation
