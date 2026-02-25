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
import streamlit as st
import urllib.parse
import db_auth

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
    oncology_constraints,
    anti_infective_constraints,
    metabolic_disease_constraints,
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

# Initialize Database
try:
    db_auth.init_db()
except Exception as e:
    st.error(f"Database initialization failed: {e}")

# Custom CSS for Hamburger Menu
st.markdown("""
<style>
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] {
        color: #FF4B4B;
        transform: scale(1.5);
    }
</style>
""", unsafe_allow_html=True)

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
    "Oncology": {
        "fn": oncology_constraints,
        "description": "Anti-cancer constraints: logP, MW, hERG, CYP3A4, therapeutic index",
        "targets": "Small-molecule anti-cancer agents, kinase inhibitors"
    },
    "Anti-Infective": {
        "fn": anti_infective_constraints,
        "description": "Antibacterial/antiviral constraints: Gram-negative penetration, low PPB, solubility",
        "targets": "Antibiotics, antifungals, antiparasitics"
    },
    "Metabolic Disease": {
        "fn": metabolic_disease_constraints,
        "description": "Diabetes/metabolic syndrome: chronic dosing, CYP3A4 safety, oral bioavailability",
        "targets": "Anti-diabetics, anti-obesity, lipid-lowering agents"
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
    "Reasoning Systems Should Know Their Limits "
    "**No generation. Design Fails Here — Safely. Clarity Through Constraint**"
)

st.markdown("---")


# -----------------------------
# Sidebar: Configuration
# -----------------------------

if 'user' not in st.session_state:
    st.session_state['user'] = None

with st.sidebar:
    st.header("👤 Account")
    if st.session_state['user']:
        st.success(f"Welcome, **{st.session_state['user']}**!")
        if st.button("Sign Out"):
            st.session_state['user'] = None
            st.rerun()
    else:
        auth_mode = st.radio("Access", ["Sign In", "Register"], label_visibility="collapsed")

        if auth_mode == "Sign In":
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In")
                if submitted:
                    if db_auth.authenticate_user(username, password):
                        st.session_state['user'] = username
                        st.rerun()
                    else:
                        st.error("Invalid username or password")

        else:  # Register
            with st.form("register_form"):
                new_user = st.text_input("Username")
                new_email = st.text_input("Email")
                new_pass = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Register")
                if submitted:
                    if len(new_pass) < 8:
                        st.error("Password must be at least 8 characters.")
                    elif db_auth.register_user(new_user, new_email, new_pass):
                        st.success("Registration successful! Please sign in.")
                    else:
                        st.error("Username or email already exists.")

    st.markdown("---")

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

    # Input Mode
    st.subheader("Input Method")
    input_mode = st.radio(
        "Mode",
        ["Calculator", "JSON"],
        index=0,
        help="Choose between form-based calculator or raw JSON input"
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

    # AILEE Integration
    st.subheader("AILEE Integration")
    use_ailee = st.toggle(
        "AILEE",
        value=False,
        help="Enable AILEE Trust Layer for deterministic evaluation confidence"
    )

    if input_mode == "JSON":
        st.markdown("---")
        # File upload only in JSON mode
        st.subheader("📄 Upload Candidate")
        uploaded = st.file_uploader(
            "Upload JSON file",
            type=["json"],
            help="Upload a candidate definition in JSON format"
        )
    else:
        uploaded = None


# -----------------------------
# Authentication Guard
# -----------------------------

if not st.session_state['user']:
    st.info("Please sign in or register to access the CuraFrame Console.")
    st.stop()


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

if input_mode == "Calculator":
    st.caption("Enter candidate properties below. Fields are derived from the selected constraint bundle.")

    # Dynamic Form Generation
    constraints = bundle_info["fn"]()
    property_names = sorted(list(set(c.name for c in constraints)))

    form_properties = {}

    cols = st.columns(2)
    for i, prop in enumerate(property_names):
        col = cols[i % 2]
        with col:
            val = st.number_input(
                f"{prop}",
                key=f"calc_{prop}",
                value=0.0,
                format="%.2f"
            )
            form_properties[prop] = val

    # Construct JSON from form
    candidate_dict = {
        "name": "calculator_candidate",
        "properties": form_properties,
        "provenance": "user_input_calculator"
    }
    candidate_text = json.dumps(candidate_dict, indent=2)

else:
    # JSON Mode
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

        # Store in session state
        st.session_state['last_result'] = result
        st.session_state['last_candidate'] = cand
        st.session_state['last_cura'] = cura
        st.session_state['last_bundle'] = bundle_name
        st.session_state['last_pop'] = pop_arg
        st.session_state['last_strict'] = strict

    except json.JSONDecodeError as e:
        st.error(f"❌ **Invalid JSON:** {e}")
        st.code(candidate_text, language="json")
    except Exception as e:
        st.error(f"❌ **Evaluation failed:** {e}")
        st.exception(e)

if 'last_result' in st.session_state:
    result = st.session_state['last_result']
    cand = st.session_state['last_candidate']
    cura = st.session_state['last_cura']
    # Use stored config for consistency in display

    try:
        # Display results
        st.markdown("---")
        st.header("📊 Evaluation Results")

        # AILEE Trust Score (deterministic: based on constraint confidence data)
        if use_ailee:
            if result.status == EvaluationStatus.ACCEPTED:
                # Trust bounded by the least-certain constraint (weakest link)
                confidences = [
                    c.provenance.confidence if c.provenance else 1.0
                    for c in cura.safety_constraints
                ]
                trust_score = min(confidences) if confidences else 0.0
            elif result.status == EvaluationStatus.REJECTED:
                # Trust in rejection based on the most confident violation
                trust_score = max(
                    (v.confidence for v in result.violations), default=0.0
                )
            else:  # INDETERMINATE
                trust_score = 0.0
            st.info(f"🛡️ **AILEE Trust Score:** {trust_score:.2f}")

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

            # Email Button
            subject = f"CuraFrame Result: {cand.name} - {result.status.value.upper()}"
            body = result.summary()

            # Simple mailto link
            mailto_link = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

            st.markdown(
                f"""
                <a href="{mailto_link}" target="_blank">
                    <button style="
                        display: inline-flex;
                        -webkit-box-align: center;
                        align-items: center;
                        -webkit-box-pack: center;
                        justify-content: center;
                        font-weight: 400;
                        padding: 0.25rem 0.75rem;
                        border-radius: 0.25rem;
                        margin: 0px;
                        line-height: 1.6;
                        color: rgb(49, 51, 63);
                        background-color: rgb(255, 255, 255);
                        width: auto;
                        border: 1px solid rgba(49, 51, 63, 0.2);
                        cursor: pointer;
                        text-decoration: none;
                    ">
                    📧 Email Results
                    </button>
                </a>
                """,
                unsafe_allow_html=True
            )

        with col_export:
            st.subheader("Export")

            if st.button("💾 Save to History", type="primary", use_container_width=True):
                if db_auth.save_log(st.session_state['user'], cand.properties, bundle_name, result.status.value):
                    st.success("Saved to history!")
                else:
                    st.error("Failed to save.")

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
                "⬇️ Download Results (JSON)",
                data=json.dumps(export_data, indent=2),
                file_name=f"curaframe_result_{cand.name}.json",
                mime="application/json",
                use_container_width=True
            )

            # Export summary as plain text (easy log sharing)
            st.download_button(
                "⬇️ Download Summary (Text)",
                data=result.summary(),
                file_name=f"curaframe_summary_{cand.name}.txt",
                mime="text/plain",
                use_container_width=True
            )

            # Export constraint metadata
            st.download_button(
                "⬇️ Download Constraints (JSON)",
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
        - **Calculator mode:** Enter property values directly via form fields
        - **JSON mode:** Enter properties as JSON, use examples as templates, or upload from file

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
    "See `PHILOSOPHY.md` for framework principles | "
    "[MIT License](https://github.com/dfeen87/CuraFrame/blob/main/LICENSE)"
)
