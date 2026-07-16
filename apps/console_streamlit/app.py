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

ALL_PARAMETERS = [
    "logP",
    "molecular_weight",
    "polar_surface_area",
    "hydrogen_bond_donors",
    "hydrogen_bond_acceptors",
    "hERG_IC50",
    "delta_QTc_ms",
    "beta1_selectivity",
    "Kd_5HT1A",
    "Kd_5HT2A",
    "Kd_D2",
    "plasma_half_life",
    "oral_bioavailability",
    "hepatic_clearance",
    "clearance",
    "CYP3A4_IC50",
    "therapeutic_index",
    "protein_binding",
    "aqueous_solubility"
]

def make_custom_modifier(operator: str, value: float):
    """
    Compile a structured operator and value into a callable CuraFrame modifier.
    Handles both scalar thresholds and tuple (range) thresholds correctly.
    """
    def modifier_fn(c):
        threshold = c.threshold
        if isinstance(threshold, tuple):
            if len(threshold) == 2:
                lower, upper = threshold
                if operator == "Override":
                    return (lower, value)
                elif operator == "*":
                    return (lower, upper * value)
                elif operator == "/":
                    divisor = value if value != 0 else 1.0
                    return (lower, upper / divisor)
                elif operator == "+":
                    return (lower, upper + value)
                elif operator == "-":
                    return (lower, upper - value)
            return threshold
        else:
            if operator == "Override":
                return value
            elif operator == "*":
                return threshold * value
            elif operator == "/":
                divisor = value if value != 0 else 1.0
                return threshold / divisor
            elif operator == "+":
                return threshold + value
            elif operator == "-":
                return threshold - value
        return threshold
    return modifier_fn


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
    selected_bundles = st.multiselect(
        "Constraint Bundles",
        list(BUNDLES.keys()),
        default=list(BUNDLES.keys()),
        help="Select constraint bundles to include in multi-bundle analysis"
    )

    if not selected_bundles:
        st.warning("Please select at least one constraint bundle.")
        st.stop()

    bundle_name = st.selectbox(
        "Active Bundle for Single-Evaluation/Sweep",
        selected_bundles,
        help="Choose one of the selected bundles to focus on for Candidate Evaluation and Parameter Sweep"
    )

    # Show bundle description
    bundle_info = BUNDLES[bundle_name]
    st.info(
        f"**Description:** {bundle_info['description']}\n\n"
        f"**Use for:** {bundle_info['targets']}"
    )

    st.markdown("---")

    # Input Mode (Hardcoded to Calculator mode as per constraints)
    input_mode = "Calculator"

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

    custom_pops = []
    if st.session_state.get('user'):
        try:
            custom_pops = db_auth.get_custom_populations(st.session_state['user'])
        except Exception as e:
            st.error(f"Failed to load custom populations: {e}")

    if use_population:
        pop_list = [""] + list(POPULATION_MODIFIERS.keys()) + [p["name"] for p in custom_pops]
        population = st.selectbox(
            "Population",
            pop_list,
            help="Apply constraint adjustments for specific patient populations"
        )

        selected_custom_pop = next((p for p in custom_pops if p["name"] == population), None)

        if population and population in POPULATION_MODIFIERS:
            st.caption(f"ℹ️ {POPULATION_MODIFIERS[population]['description']}")
        elif selected_custom_pop:
            st.caption(f"ℹ️ {selected_custom_pop['description'] or 'Custom user-defined patient population.'}")
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

st.caption("Enter candidate properties below. Fields are derived from the selected constraint bundle.")

# Dynamic Form Generation
all_selected_constraints = []
for b_name in selected_bundles:
    all_selected_constraints.extend(BUNDLES[b_name]["fn"]())

property_names = sorted(list(set(c.name for c in all_selected_constraints)))

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


# -----------------------------
# Tabs Configuration
# -----------------------------

st.markdown("---")

tab_eval, tab_sweep, tab_custom, tab_matrix = st.tabs([
    "🔍 Candidate Evaluation",
    "📈 Parameter Sweep & Boundary Mapping",
    "👥 Custom Population Profiles",
    "📊 Multi-Bundle Matrix"
])

with tab_eval:
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
            if use_population and population:
                if population in POPULATION_MODIFIERS:
                    pop_mods = {
                        k: v for k, v in POPULATION_MODIFIERS[population].items()
                        if k != "description"
                    }
                    cura.add_population(population, pop_mods)
                else:
                    # Query custom population details
                    custom_pops = db_auth.get_custom_populations(st.session_state['user'])
                    selected_custom_pop = next((p for p in custom_pops if p["name"] == population), None)
                    if selected_custom_pop:
                        pop_mods = {}
                        for mod in selected_custom_pop["modifiers"]:
                            param = mod["parameter"]
                            op = mod["operator"]
                            val = mod["value"]
                            pop_mods[param] = make_custom_modifier(op, val)
                            # Support mapping clearance to hepatic_clearance and vice versa
                            if param == "clearance":
                                pop_mods["hepatic_clearance"] = make_custom_modifier(op, val)
                            elif param == "hepatic_clearance":
                                pop_mods["clearance"] = make_custom_modifier(op, val)
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
                export_pop_profile = None
                if pop_arg and pop_arg not in POPULATION_MODIFIERS:
                    custom_pops = db_auth.get_custom_populations(st.session_state['user'])
                    matched_pop = next((p for p in custom_pops if p["name"] == pop_arg), None)
                    if matched_pop:
                        export_pop_profile = {
                            "name": matched_pop["name"],
                            "description": matched_pop["description"],
                            "modifiers": matched_pop["modifiers"]
                        }

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
                        "population_profile": export_pop_profile,
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

            # Logical Failure Diagnostic & Gap Analysis UI integration
            if result.status == EvaluationStatus.REJECTED and result.gap_analysis:
                st.markdown("---")
                st.header("🔬 Logical Failure Diagnostic & Gap Analysis")
                st.info(
                    "**Under current simulation parameters, target constraint boundaries are violated.** "
                    "The following structured parameter adjustments are scientifically advised to resolve compliance gaps."
                )

                # Gather flat numeric gaps to display in a summary table
                flat_gaps = []

                def _gather_flat_gaps_recursive(node: Dict[str, Any], path_prefix: str = "") -> None:
                    if "logic" in node:
                        group_name = node.get("name", "Root Bundle")
                        prefix = f"{path_prefix} ➡️ {group_name}" if path_prefix else group_name
                        # Handle both standard 'children' and root level 'constraints' key
                        children = node.get("children", node.get("constraints", []))
                        for child in children:
                            _gather_flat_gaps_recursive(child, prefix)
                    else:
                        if node.get("status") == "Failed":
                            flat_gaps.append({
                                "Context": path_prefix or "Core Bundle",
                                "Parameter": node.get("name", "Unknown"),
                                "Observed": node.get("observed"),
                                "Threshold": str(node.get("threshold")),
                                "Required Adjustment": node.get("message", "Violates constraint.")
                            })

                _gather_flat_gaps_recursive(result.gap_analysis)

                if flat_gaps:
                    import pandas as pd
                    df_gaps = pd.DataFrame(flat_gaps)
                    st.dataframe(df_gaps, use_container_width=True, hide_index=True)
                else:
                    st.write("• No numeric parameter gaps detected.")

                # Render a collapsible section showing the full logical tree layout of the failure pathways
                with st.expander("📋 View Logical Constraint Decision Tree & Pathways", expanded=False):
                    def _render_tree_node(node: Dict[str, Any], level: int = 0):
                        indent = "&nbsp;" * (level * 8)
                        status_emoji = "✅" if node.get("status") == "Passed" else ("❌" if node.get("status") == "Failed" else "⚠️")

                        if "logic" in node:
                            group_name = node.get("name", "Root Bundle")
                            st.markdown(
                                f"{indent}{status_emoji} **Group: `{group_name}`** (Logic: `{node['op'] if 'op' in node else node['logic']}` — `{node['status']}`)",
                                unsafe_allow_html=True
                            )
                            children = node.get("children", node.get("constraints", []))
                            for child in children:
                                _render_tree_node(child, level + 1)
                        else:
                            st.markdown(
                                f"{indent}{status_emoji} `{node['name']}`: observed `{node.get('observed')}`, required `{node.get('threshold')}`",
                                unsafe_allow_html=True
                            )
                            if node.get("status") == "Failed" and "message" in node:
                                st.markdown(
                                    f"{indent}&nbsp;&nbsp;&nbsp;&nbsp;➡️ *{node['message']}*",
                                    unsafe_allow_html=True
                                )

                    _render_tree_node(result.gap_analysis)

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


with tab_sweep:
    st.header("📈 Parameter Sweep & Boundary Mapping")
    st.caption("Map the safety boundaries of the hypothetical design by sweeping properties across specified ranges.")

    # Get available properties for the selected bundle
    constraints = bundle_info["fn"]()
    property_names = sorted(list(set(c.name for c in constraints)))

    if not property_names:
        st.warning("No properties available in this constraint bundle to sweep.")
    else:
        col_sweep_cfg, col_sweep_run = st.columns([2, 1])

        with col_sweep_cfg:
            sweep_type = st.radio("Sweep Dimension", ["1D Sweep", "2D Sweep"], horizontal=True, key="sweep_type_radio")

            if sweep_type == "1D Sweep":
                sweep_prop = st.selectbox("Select Property to Sweep", property_names, key="sweep_prop_select")

                # Provide sensible default min/max based on property name
                default_min = 0.0
                default_max = 10.0
                if sweep_prop == "logP":
                    default_min, default_max = 0.0, 6.0
                elif "IC50" in sweep_prop:
                    default_min, default_max = 0.0, 40.0
                elif "selectivity" in sweep_prop:
                    default_min, default_max = 0.0, 300.0
                elif "weight" in sweep_prop:
                    default_min, default_max = 100.0, 600.0
                elif "area" in sweep_prop:
                    default_min, default_max = 20.0, 150.0
                elif "half_life" in sweep_prop:
                    default_min, default_max = 0.0, 36.0
                elif "bioavailability" in sweep_prop:
                    default_min, default_max = 0.0, 100.0
                elif "binding" in sweep_prop:
                    default_min, default_max = 50.0, 100.0
                elif "solubility" in sweep_prop:
                    default_min, default_max = 0.0, 200.0
                elif "Kd" in sweep_prop:
                    default_min, default_max = 0.0, 2000.0

                col_range_min, col_range_max, col_range_steps = st.columns(3)
                with col_range_min:
                    sweep_min = st.number_input("Min Value", value=default_min, format="%.2f", key="sweep_min_input")
                with col_range_max:
                    sweep_max = st.number_input("Max Value", value=default_max, format="%.2f", key="sweep_max_input")
                with col_range_steps:
                    sweep_steps = st.number_input("Steps", value=20, min_value=2, max_value=100, key="sweep_steps_input")

            else:  # 2D Sweep
                sweep_prop1 = st.selectbox("Select Property 1 (X-axis)", property_names, index=0, key="sweep_prop1_select")
                sweep_prop2 = st.selectbox("Select Property 2 (Y-axis)", property_names, index=min(1, len(property_names)-1), key="sweep_prop2_select")

                # Default ranges
                default_min1, default_max1 = 0.0, 10.0
                if sweep_prop1 == "logP":
                    default_min1, default_max1 = 0.0, 6.0
                elif "IC50" in sweep_prop1:
                    default_min1, default_max1 = 0.0, 40.0
                elif "selectivity" in sweep_prop1:
                    default_min1, default_max1 = 0.0, 300.0

                default_min2, default_max2 = 0.0, 10.0
                if sweep_prop2 == "logP":
                    default_min2, default_max2 = 0.0, 6.0
                elif "IC50" in sweep_prop2:
                    default_min2, default_max2 = 0.0, 40.0
                elif "selectivity" in sweep_prop2:
                    default_min2, default_max2 = 0.0, 300.0

                col_range_min1, col_range_max1, col_range_steps1 = st.columns(3)
                with col_range_min1:
                    sweep_min1 = st.number_input("Prop 1 Min", value=default_min1, format="%.2f", key="sweep_min1_input")
                with col_range_max1:
                    sweep_max1 = st.number_input("Prop 1 Max", value=default_max1, format="%.2f", key="sweep_max1_input")
                with col_range_steps1:
                    sweep_steps1 = st.number_input("Prop 1 Steps", value=10, min_value=2, max_value=30, key="sweep_steps1_input")

                col_range_min2, col_range_max2, col_range_steps2 = st.columns(3)
                with col_range_min2:
                    sweep_min2 = st.number_input("Prop 2 Min", value=default_min2, format="%.2f", key="sweep_min2_input")
                with col_range_max2:
                    sweep_max2 = st.number_input("Prop 2 Max", value=default_max2, format="%.2f", key="sweep_max2_input")
                with col_range_steps2:
                    sweep_steps2 = st.number_input("Prop 2 Steps", value=10, min_value=2, max_value=30, key="sweep_steps2_input")

        with col_sweep_run:
            st.markdown("<br><br>", unsafe_allow_html=True)
            run_sweep_button = st.button("🚀 Run Parameter Sweep", type="primary", use_container_width=True, key="run_sweep_btn")
            compare_populations = False
            if sweep_type == "1D Sweep" and use_population and population:
                compare_populations = st.checkbox("Compare with General Population", value=True, key="compare_pop_chk")

        if run_sweep_button:
            try:
                # Import sweep logic
                from cura_frame.sensitivity import run_1d_sweep, run_2d_sweep, find_inflection_points
                import pandas as pd
                import altair as alt

                # Parse candidate JSON
                raw = json.loads(candidate_text)
                cand = Candidate(
                    name=raw.get("name", "unnamed"),
                    properties=raw.get("properties", {}),
                    provenance=raw.get("provenance")
                )

                # Build framework and register population modifiers
                constraints = bundle_info["fn"]()
                cura = CuraFrame(constraints, name=f"CuraFrame::{bundle_name}")
                if use_population and population:
                    if population in POPULATION_MODIFIERS:
                        pop_mods = {k: v for k, v in POPULATION_MODIFIERS[population].items() if k != "description"}
                        cura.add_population(population, pop_mods)
                    else:
                        custom_pops = db_auth.get_custom_populations(st.session_state['user'])
                        selected_custom_pop = next((p for p in custom_pops if p["name"] == population), None)
                        if selected_custom_pop:
                            pop_mods = {}
                            for mod in selected_custom_pop["modifiers"]:
                                param = mod["parameter"]
                                op = mod["operator"]
                                val = mod["value"]
                                pop_mods[param] = make_custom_modifier(op, val)
                                if param == "clearance":
                                    pop_mods["hepatic_clearance"] = make_custom_modifier(op, val)
                                elif param == "hepatic_clearance":
                                    pop_mods["clearance"] = make_custom_modifier(op, val)
                            cura.add_population(population, pop_mods)

                pop_arg = population if use_population else None

                st.markdown("---")
                st.subheader("📊 Sweep Results & Analysis")

                if sweep_type == "1D Sweep":
                    if compare_populations and pop_arg:
                        results_gen = run_1d_sweep(cura, cand, sweep_prop, sweep_min, sweep_max, sweep_steps, population=None, strict=strict)
                        results_pop = run_1d_sweep(cura, cand, sweep_prop, sweep_min, sweep_max, sweep_steps, population=pop_arg, strict=strict)

                        df_gen = pd.DataFrame(results_gen)
                        df_gen['Population'] = 'General'

                        df_pop = pd.DataFrame(results_pop)
                        df_pop['Population'] = pop_arg.capitalize()

                        df_all = pd.concat([df_gen, df_pop])
                        df_all['status_str'] = df_all['status'].apply(lambda s: s.value.upper())

                        # Interactive plot with columns/facets
                        chart = alt.Chart(df_all).mark_point(size=120, filled=True).encode(
                            x=alt.X('value:Q', title=sweep_prop),
                            y=alt.Y('status_str:N', title='Status', sort=['ACCEPTED', 'INDETERMINATE', 'REJECTED']),
                            color=alt.Color('status_str:N', scale=alt.Scale(
                                domain=['ACCEPTED', 'INDETERMINATE', 'REJECTED'],
                                range=['#2ecc71', '#f39c12', '#e74c3c']
                            ), title="Status"),
                            shape=alt.Shape('Population:N', title="Population Context"),
                            row=alt.Row('Population:N', title='Population Context'),
                            tooltip=['value', 'status_str', 'violations']
                        ).properties(
                            height=150,
                            width=600
                        ).interactive()

                        st.altair_chart(chart, use_container_width=True)

                        # Show Inflection points for both
                        col_infl_gen, col_infl_pop = st.columns(2)
                        with col_infl_gen:
                            st.write("**General Population Transitions:**")
                            inflections_gen = find_inflection_points(results_gen)
                            if inflections_gen:
                                for inf in inflections_gen:
                                    st.success(f"Boundary: `{inf['value_from']:.2f}` to `{inf['value_to']:.2f}`")
                                    st.write(f"Transition: `{inf['status_from'].value.upper()}` ➡️ `{inf['status_to'].value.upper()}`")
                                    if inf['violations_to']:
                                        st.write(f"Violations triggered: {', '.join(inf['violations_to'])}")
                            else:
                                st.info("No transitions detected across the sweep range.")

                        with col_infl_pop:
                            st.write(f"**{pop_arg.capitalize()} Population Transitions:**")
                            inflections_pop = find_inflection_points(results_pop)
                            if inflections_pop:
                                for inf in inflections_pop:
                                    st.success(f"Boundary: `{inf['value_from']:.2f}` to `{inf['value_to']:.2f}`")
                                    st.write(f"Transition: `{inf['status_from'].value.upper()}` ➡️ `{inf['status_to'].value.upper()}`")
                                    if inf['violations_to']:
                                        st.write(f"Violations triggered: {', '.join(inf['violations_to'])}")
                            else:
                                st.info("No transitions detected across the sweep range.")
                    else:
                        # Non-comparison 1D sweep
                        results = run_1d_sweep(cura, cand, sweep_prop, sweep_min, sweep_max, sweep_steps, population=pop_arg, strict=strict)
                        df = pd.DataFrame(results)
                        df['status_str'] = df['status'].apply(lambda s: s.value.upper())

                        chart = alt.Chart(df).mark_point(size=120, filled=True).encode(
                            x=alt.X('value:Q', title=sweep_prop),
                            y=alt.Y('status_str:N', title='Status', sort=['ACCEPTED', 'INDETERMINATE', 'REJECTED']),
                            color=alt.Color('status_str:N', scale=alt.Scale(
                                domain=['ACCEPTED', 'INDETERMINATE', 'REJECTED'],
                                range=['#2ecc71', '#f39c12', '#e74c3c']
                            ), title="Status"),
                            tooltip=['value', 'status_str', 'violations']
                        ).properties(
                            height=250,
                            width=600
                        ).interactive()

                        st.altair_chart(chart, use_container_width=True)

                        st.write("**Transitions / Boundaries Detected:**")
                        inflections = find_inflection_points(results)
                        if inflections:
                            for inf in inflections:
                                st.success(f"Boundary: `{inf['value_from']:.2f}` to `{inf['value_to']:.2f}`")
                                st.write(f"Transition: `{inf['status_from'].value.upper()}` ➡️ `{inf['status_to'].value.upper()}`")
                                if inf['violations_to']:
                                    st.write(f"Violations triggered: {', '.join(inf['violations_to'])}")
                        else:
                            st.info("No transitions detected across the sweep range.")

                else:
                    # 2D Sweep
                    results = run_2d_sweep(
                        cura, cand, sweep_prop1, sweep_min1, sweep_max1,
                        sweep_prop2, sweep_min2, sweep_max2,
                        sweep_steps1, sweep_steps2, population=pop_arg, strict=strict
                    )
                    df = pd.DataFrame(results)
                    df['status_str'] = df['status'].apply(lambda s: s.value.upper())

                    # Draw an Altair Rect heatmap grid
                    chart = alt.Chart(df).mark_rect().encode(
                        x=alt.X('value1:O', title=sweep_prop1, axis=alt.Axis(format=".2f")),
                        y=alt.Y('value2:O', title=sweep_prop2, axis=alt.Axis(format=".2f")),
                        color=alt.Color('status_str:N', scale=alt.Scale(
                            domain=['ACCEPTED', 'INDETERMINATE', 'REJECTED'],
                            range=['#2ecc71', '#f39c12', '#e74c3c']
                        ), title="Status"),
                        tooltip=['value1', 'value2', 'status_str', 'violations']
                    ).properties(
                        height=400,
                        width=600
                    ).interactive()

                    st.altair_chart(chart, use_container_width=True)
                    st.info("💡 Tip: Hover over the grid cells to view precise values and active violations.")

            except json.JSONDecodeError as e:
                st.error(f"❌ **Invalid JSON:** {e}")
            except Exception as e:
                st.error(f"❌ **Sweep execution failed:** {e}")
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

# -----------------------------
# Tab: Custom Population Profiles
# -----------------------------

with tab_custom:
    st.header("👥 Custom Population Profile Creator & Editor")
    st.caption("Define new, custom patient populations or comorbidity profiles by specifying parameter modifiers.")

    if 'editing_modifiers' not in st.session_state:
        st.session_state['editing_modifiers'] = []

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🛠️ Profile Editor")

        # Load existing populations for the logged-in user
        user_custom_pops = db_auth.get_custom_populations(st.session_state['user'])

        pop_editor_options = ["-- Create New Profile --"] + [p["name"] for p in user_custom_pops]
        selected_edit_pop_name = st.selectbox("Select Profile to Edit", pop_editor_options)

        # Set defaults based on selection
        if selected_edit_pop_name == "-- Create New Profile --":
            default_name = ""
            default_desc = ""
            default_modifiers = []
        else:
            found_pop = next(p for p in user_custom_pops if p["name"] == selected_edit_pop_name)
            default_name = found_pop["name"]
            default_desc = found_pop["description"]
            default_modifiers = found_pop["modifiers"]

        # Track when active editing profile changes and sync modifiers list
        if 'last_selected_edit_pop' not in st.session_state or st.session_state['last_selected_edit_pop'] != selected_edit_pop_name:
            st.session_state['last_selected_edit_pop'] = selected_edit_pop_name
            st.session_state['editing_modifiers'] = list(default_modifiers)

        # Form fields
        edit_name = st.text_input("Profile Name", value=default_name, placeholder="e.g., renal-impaired asthmatic")
        edit_desc = st.text_area("Description", value=default_desc, placeholder="e.g., Reduced clearance and doubled selectivity requirements.")

        st.write("---")
        st.subheader("➕ Add / Edit Modifiers")

        # Step 1: Dropdown to select a parameter
        mod_param = st.selectbox("1. Select Parameter", ALL_PARAMETERS)

        # Step 2: Operator dropdown
        mod_op = st.selectbox("2. Operator", ["*", "/", "+", "-", "Override"])

        # Step 3: Numeric input for factor/value
        mod_val = st.number_input("3. Value / Factor", value=1.0, format="%.4f")

        if st.button("Add Modifier to Profile"):
            # Remove any existing modifier for the same parameter to avoid duplicates
            st.session_state['editing_modifiers'] = [
                m for m in st.session_state['editing_modifiers']
                if m["parameter"] != mod_param
            ]
            st.session_state['editing_modifiers'].append({
                "parameter": mod_param,
                "operator": mod_op,
                "value": mod_val
            })
            st.success(f"Added modifier: {mod_param} {mod_op} {mod_val}")
            st.rerun()

        # Display current modifiers in the profile
        if st.session_state['editing_modifiers']:
            st.write("**Current Modifiers:**")
            for idx, m in enumerate(st.session_state['editing_modifiers']):
                col_m_text, col_m_del = st.columns([4, 1])
                with col_m_text:
                    st.write(f"- `{m['parameter']}` `{m['operator']}` `{m['value']}`")
                with col_m_del:
                    if st.button("🗑️", key=f"del_mod_{idx}"):
                        st.session_state['editing_modifiers'].pop(idx)
                        st.rerun()
        else:
            st.info("No modifiers added yet. Use the fields above to add modifiers.")

        st.write("---")
        col_btn_save, col_btn_delete = st.columns(2)

        with col_btn_save:
            if st.button("💾 Save Profile", type="primary", use_container_width=True):
                if not edit_name:
                    st.error("Profile Name cannot be empty.")
                elif not st.session_state['editing_modifiers']:
                    st.error("Please add at least one modifier.")
                else:
                    success = db_auth.save_custom_population(
                        st.session_state['user'],
                        edit_name,
                        edit_desc,
                        st.session_state['editing_modifiers']
                    )
                    if success:
                        st.success(f"Profile '{edit_name}' saved successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to save profile.")

        with col_btn_delete:
            if selected_edit_pop_name != "-- Create New Profile --":
                if st.button("🗑️ Delete Profile", use_container_width=True):
                    success = db_auth.delete_custom_population(st.session_state['user'], selected_edit_pop_name)
                    if success:
                        st.success(f"Profile '{selected_edit_pop_name}' deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete profile.")

    with col_right:
        st.subheader("👁️ Profile Preview & Export")
        if edit_name:
            st.write(f"**Name:** {edit_name}")
            st.write(f"**Description:** {edit_desc or '*No description provided*'}")

            profile_json_data = {
                "name": edit_name,
                "description": edit_desc,
                "created_by": st.session_state['user'],
                "modifiers": st.session_state['editing_modifiers']
            }

            st.download_button(
                "⬇️ Download Population Profile (JSON)",
                data=json.dumps(profile_json_data, indent=2),
                file_name=f"population_profile_{edit_name.replace(' ', '_').lower()}.json",
                mime="application/json",
                use_container_width=True
            )

            st.code(json.dumps(profile_json_data, indent=2), language="json")
        else:
            st.info("Provide a profile name to see preview & enable export.")

        st.write("---")
        st.subheader("🧪 Quick Test Evaluation")
        st.caption("Test the active modifiers against a sample candidate using the active constraint bundle.")

        test_bundle_name = st.selectbox("Select Bundle for Test", list(BUNDLES.keys()), key="test_bundle_select")

        # Create a sample candidate for the chosen bundle
        test_bundle_fn = BUNDLES[test_bundle_name]["fn"]
        test_constraints = test_bundle_fn()
        test_prop_names = sorted(list(set(c.name for c in test_constraints)))

        sample_props = {}
        for p in test_prop_names:
            if p == "logP":
                sample_props[p] = 3.0
            elif "IC50" in p or "ic50" in p:
                sample_props[p] = 15.0
            elif "selectivity" in p:
                sample_props[p] = 120.0
            elif "weight" in p or "mw" in p:
                sample_props[p] = 400.0
            elif "area" in p or "psa" in p:
                sample_props[p] = 70.0
            elif "half_life" in p:
                sample_props[p] = 12.0
            elif "binding" in p:
                sample_props[p] = 80.0
            elif "solubility" in p:
                sample_props[p] = 50.0
            elif "bioavailability" in p:
                sample_props[p] = 50.0
            elif "Kd" in p:
                sample_props[p] = 12.0
            else:
                sample_props[p] = 10.0

        if st.button("🧪 Run Test Evaluation", use_container_width=True):
            if not st.session_state['editing_modifiers']:
                st.warning("Please add at least one modifier to test.")
            else:
                test_cand = Candidate(
                    name="Test_Sample_Candidate",
                    properties=sample_props,
                    provenance="quick_test_evaluation"
                )

                # Setup CuraFrame
                test_cura = CuraFrame(test_constraints, name=f"CuraFrame::Test::{test_bundle_name}")

                # Compile modifiers
                test_pop_mods = {}
                for mod in st.session_state['editing_modifiers']:
                    param = mod["parameter"]
                    op = mod["operator"]
                    val = mod["value"]
                    test_pop_mods[param] = make_custom_modifier(op, val)
                    if param == "clearance":
                        test_pop_mods["hepatic_clearance"] = make_custom_modifier(op, val)
                    elif param == "hepatic_clearance":
                        test_pop_mods["clearance"] = make_custom_modifier(op, val)

                test_cura.add_population("test_pop", test_pop_mods)
                test_result = test_cura.evaluate(test_cand, population="test_pop", strict=False)

                st.markdown(f"**Test Result:** `{test_result.status.value.upper()}`")
                st.code(test_result.summary(), language="text")


# -----------------------------
# Tab: Multi-Bundle Matrix
# -----------------------------

with tab_matrix:
    st.header("📊 Multi-Bundle Evaluation Matrix")
    st.caption("Evaluate a single candidate against all (or multiple selected) constraint bundles simultaneously.")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        generate_matrix_button = st.button(
            "📊 Generate Multi-Bundle Matrix",
            type="primary",
            use_container_width=True,
            key="generate_matrix_btn"
        )
    with col_info:
        st.caption(
            "Runs evaluations across all selected bundles using the candidate properties defined above."
        )

    # We want to display the last generated results if they are in session state
    if generate_matrix_button:
        try:
            # Parse candidate JSON
            raw = json.loads(candidate_text)
            cand = Candidate(
                name=raw.get("name", "unnamed"),
                properties=raw.get("properties", {}),
                provenance=raw.get("provenance")
            )

            matrix_results = {}
            for b_name in selected_bundles:
                constraints = BUNDLES[b_name]["fn"]()
                cura = CuraFrame(constraints, name=f"CuraFrame::{b_name}")

                # Register population modifiers
                if use_population and population:
                    if population in POPULATION_MODIFIERS:
                        pop_mods = {
                            k: v for k, v in POPULATION_MODIFIERS[population].items()
                            if k != "description"
                        }
                        cura.add_population(population, pop_mods)
                    else:
                        custom_pops = db_auth.get_custom_populations(st.session_state['user'])
                        selected_custom_pop = next((p for p in custom_pops if p["name"] == population), None)
                        if selected_custom_pop:
                            pop_mods = {}
                            for mod in selected_custom_pop["modifiers"]:
                                param = mod["parameter"]
                                op = mod["operator"]
                                val = mod["value"]
                                pop_mods[param] = make_custom_modifier(op, val)
                                if param == "clearance":
                                    pop_mods["hepatic_clearance"] = make_custom_modifier(op, val)
                                elif param == "hepatic_clearance":
                                    pop_mods["clearance"] = make_custom_modifier(op, val)
                            cura.add_population(population, pop_mods)

                # Evaluate
                pop_arg = population if use_population else None
                result = cura.evaluate(cand, population=pop_arg, strict=strict)
                matrix_results[b_name] = {
                    "result": result,
                    "cura": cura
                }

            # Save to session state
            st.session_state['last_matrix_results'] = matrix_results
            st.session_state['last_matrix_candidate'] = cand
            st.session_state['last_matrix_bundles'] = selected_bundles
            st.session_state['last_matrix_pop'] = population if use_population else None
            st.session_state['last_matrix_strict'] = strict

        except Exception as e:
            st.error(f"❌ **Multi-bundle evaluation failed:** {e}")
            st.exception(e)

    if 'last_matrix_results' in st.session_state:
        matrix_results = st.session_state['last_matrix_results']
        cand = st.session_state['last_matrix_candidate']
        active_bundles = st.session_state['last_matrix_bundles']
        pop_arg = st.session_state['last_matrix_pop']
        strict_val = st.session_state['last_matrix_strict']

        import pandas as pd

        # -----------------------------
        # Layer 1: Summary Table
        # -----------------------------
        st.markdown("---")
        st.subheader("📋 Layer 1: Summary Table")

        summary_data = []
        for b_name in active_bundles:
            if b_name not in matrix_results:
                continue
            b_info = matrix_results[b_name]
            res = b_info["result"]

            if res.status == EvaluationStatus.ACCEPTED:
                emoji_status = "🟢 ACCEPTED"
            elif res.status == EvaluationStatus.REJECTED:
                emoji_status = "🔴 REJECTED"
            else:
                emoji_status = "🟡 INDET"

            violated_params = ", ".join(sorted(list(set(v.constraint for v in res.violations)))) if res.violations else "None"
            summary_data.append({
                "Bundle Name": b_name,
                "Overall Status": emoji_status,
                "Violations Count": len(res.violations),
                "Violated Parameters": violated_params
            })

        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)

        # -----------------------------
        # Layer 2: Constraint Grid
        # -----------------------------
        st.markdown("---")
        st.subheader("🎯 Layer 2: Constraint Grid")

        # Get dynamic union of parameters
        all_constraints = []
        for b_name in active_bundles:
            all_constraints.extend(BUNDLES[b_name]["fn"]())
        unique_params = sorted(list(set(c.name for c in all_constraints)))

        grid_data = []
        for prop in unique_params:
            row = {"Parameter": prop}
            for b_name in active_bundles:
                if b_name not in matrix_results:
                    row[b_name] = "⚪ —"
                    continue
                b_info = matrix_results[b_name]
                cura = b_info["cura"]
                res = b_info["result"]

                c_obj = cura.get_constraint(prop)
                if c_obj is None:
                    row[b_name] = "⚪ —"
                else:
                    if cand.get(prop) is None:
                        row[b_name] = "🟡 INDET"
                    else:
                        is_violated = any(v.constraint == prop for v in res.violations)
                        if is_violated:
                            row[b_name] = "🔴 FAIL"
                        else:
                            row[b_name] = "🟢 PASS"
            grid_data.append(row)

        df_grid = pd.DataFrame(grid_data)

        def style_cells(val):
            if val == "🟢 PASS":
                return "background-color: #d4edda; color: #155724; font-weight: bold;"
            elif val == "🔴 FAIL":
                return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
            elif val == "🟡 INDET":
                return "background-color: #fff3cd; color: #856404; font-weight: bold;"
            elif val == "⚪ —":
                return "background-color: #e2e3e5; color: #383d41;"
            return ""

        if hasattr(df_grid.style, "map"):
            styled_grid = df_grid.style.map(style_cells, subset=active_bundles)
        else:
            styled_grid = df_grid.style.applymap(style_cells, subset=active_bundles)

        st.dataframe(styled_grid, use_container_width=True, hide_index=True)

        # -----------------------------
        # Cross-Therapeutic Profile Warnings
        # -----------------------------
        st.markdown("---")
        st.subheader("⚠️ Cross-Therapeutic Profile Warnings")

        cross_warnings = []
        accepted_list = []
        rejected_list = []

        for b_name in active_bundles:
            if b_name not in matrix_results:
                continue
            res = matrix_results[b_name]["result"]
            if res.status == EvaluationStatus.ACCEPTED:
                accepted_list.append(b_name)
            elif res.status == EvaluationStatus.REJECTED:
                rejected_list.append(b_name)

        for acc in accepted_list:
            for rej in rejected_list:
                rej_info = matrix_results[rej]
                crit_violations = [v for v in rej_info["result"].violations if v.severity == Severity.CRITICAL]
                for cv in crit_violations:
                    title = "Cross-Therapeutic Warning"
                    if "Cardiol" in rej:
                        title = "Cardiac Risk Warning"
                    elif "CNS" in rej:
                        title = "CNS Safety Warning"
                    elif "Safety" in rej:
                        title = "Core Safety Warning"

                    warning_text = (
                        f"**{title}:** Candidate meets **{acc}** criteria but fails **{rej}** constraints "
                        f"due to a CRITICAL violation: **{cv.constraint}** (observed: {cv.observed}, required: {cv.threshold}). "
                        f"\n\n*Rationale:* {cv.rationale}"
                    )
                    cross_warnings.append(warning_text)

        if cross_warnings:
            for cw in cross_warnings:
                st.warning(cw)
        else:
            st.success("No cross-therapeutic profile warnings detected. Candidate profile is consistent across all evaluated domains.")

        # -----------------------------
        # Export Capabilities
        # -----------------------------
        st.markdown("---")
        st.subheader("💾 Export Options")

        col_exp1, col_exp2, col_exp3 = st.columns(3)

        with col_exp1:
            # JSON Export
            export_json_data = {
                "candidate": {
                    "name": cand.name,
                    "properties": cand.properties,
                    "provenance": cand.provenance
                },
                "configuration": {
                    "population": pop_arg,
                    "strict": strict_val,
                    "evaluated_bundles": active_bundles
                },
                "matrix_summary": summary_data,
                "grid": grid_data,
                "cross_warnings": cross_warnings
            }
            st.download_button(
                "⬇️ Download Matrix Results (JSON)",
                data=json.dumps(export_json_data, indent=2),
                file_name=f"curaframe_matrix_{cand.name}.json",
                mime="application/json",
                use_container_width=True,
                key="download_json_matrix_btn"
            )

        with col_exp2:
            # Summary Table CSV Export
            csv_summary = df_summary.to_csv(index=False)
            st.download_button(
                "⬇️ Download Summary Table (CSV)",
                data=csv_summary,
                file_name=f"curaframe_matrix_summary_{cand.name}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_csv_summary_btn"
            )

        with col_exp3:
            # Constraint Grid CSV Export
            csv_grid = df_grid.to_csv(index=False)
            st.download_button(
                "⬇️ Download Constraint Grid (CSV)",
                data=csv_grid,
                file_name=f"curaframe_matrix_grid_{cand.name}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_csv_grid_btn"
            )

# Credits
st.markdown("---")
st.caption(
    "CuraFrame Console v1.0 | "
    "Inspired by Krüger & Feeney (2025) — CardiAnx-1 Dual-Domain Concept | "
    "See `PHILOSOPHY.md` for framework principles | "
    "[MIT License](https://github.com/dfeen87/CuraFrame/blob/main/LICENSE)"
)
