"""AWS Architecture Recommender — Streamlit Web Interface.

Provides an interactive dashboard for exploring AI-driven cloud architecture
recommendations, inspecting service topologies, diagrams, estimated costs,
Well-Architected security reviews, and raw JSON artifacts.

Runs in Demo mode by default without requiring AWS credentials or network access.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import streamlit as st

# Ensure repository root and 'src' directory are on sys.path
_APP_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _APP_DIR.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Safe pipeline and helper imports
try:
    from aws_arch.common import ROOT, load_catalogue, load_json
    from aws_arch.pipeline import run_downstream, run_full
    _PIPELINE_AVAILABLE = True
    _IMPORT_ERROR = None
except Exception as _import_err:  # pragma: no cover
    _PIPELINE_AVAILABLE = False
    _IMPORT_ERROR = str(_import_err)


# -----------------------------------------------------------------------------
# Scenario Discovery
# -----------------------------------------------------------------------------
def discover_scenarios() -> dict[str, dict[str, Any]]:
    """Discover available demonstration scenarios from the 'examples/' directory.

    Matches pairs of '<prefix>_requirement.json' and '<prefix>_architecture.json'.
    Returns a dictionary mapping scenario keys to metadata and loaded JSON objects.
    """
    examples_dir = _REPO_ROOT / "examples"
    scenarios: dict[str, dict[str, Any]] = {}
    if not examples_dir.exists():
        return scenarios

    for req_path in sorted(examples_dir.glob("*_requirement.json")):
        prefix = req_path.name[: -len("_requirement.json")]
        arch_path = examples_dir / f"{prefix}_architecture.json"
        if arch_path.exists():
            try:
                req_data = load_json(req_path)
                arch_data = load_json(arch_path)
                app_type = req_data.get("app_type", prefix.replace("_", " "))
                name = f"{app_type.title()} ({arch_data.get('pattern', 'Reference').replace('_', ' ').title()})"
                scenarios[prefix] = {
                    "key": prefix,
                    "title": name,
                    "req_path": req_path,
                    "arch_path": arch_path,
                    "req": req_data,
                    "arch": arch_data,
                }
            except Exception:  # pragma: no cover
                continue
    return scenarios


# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="AWS Architecture Recommender",
        page_icon="☁️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("☁️ AWS Architecture Recommender")
    st.caption("AI-Driven Cloud Architecture Design & Well-Architected Recommendation System")

    if not _PIPELINE_AVAILABLE:  # pragma: no cover
        st.error(f"Failed to initialize core recommender pipeline: {_IMPORT_ERROR}")
        st.stop()

    # Load service catalogue for category lookup
    try:
        catalogue = load_catalogue().get("services", {})
    except Exception:
        catalogue = {}

    # Discover cached demonstration scenarios
    scenarios = discover_scenarios()

    # -------------------------------------------------------------------------
    # Sidebar: Scenario Selection & Controls
    # -------------------------------------------------------------------------
    st.sidebar.header("Demonstration Scenarios")
    demo_mode = st.sidebar.checkbox(
        "Demo mode (offline, cached examples)",
        value=True,
        help="Runs completely offline using verified repository examples without requiring AWS credentials or Bedrock access.",
        key="demo_mode_checkbox",
    )

    selected_scenario_key: str | None = None
    if scenarios:
        scenario_options = list(scenarios.keys())
        selected_scenario_key = st.sidebar.selectbox(
            "Select Cached Scenario",
            options=scenario_options,
            format_func=lambda k: scenarios[k]["title"],
            key="selected_scenario_selector",
        )
    else:
        st.sidebar.warning("No example scenarios discovered in 'examples/' directory.")

    st.sidebar.markdown("---")
    st.sidebar.subheader("About")
    st.sidebar.markdown(
        "**Cloud Architecture Design Project**\n\n"
        "- Deterministic rule-based validation\n"
        "- Well-Architected security assessment\n"
        "- Mumbai (`ap-south-1`) cost projections\n"
        "- Interactive Graphviz topology diagrams\n\n"
        "*Recommendation-only: no resources are deployed.*"
    )

    # -------------------------------------------------------------------------
    # State Management: Track Scenario Changes
    # -------------------------------------------------------------------------
    if "current_scenario" not in st.session_state:
        st.session_state["current_scenario"] = None
    if "report" not in st.session_state:
        st.session_state["report"] = None
    if "req_text" not in st.session_state:
        st.session_state["req_text"] = ""
    if "is_demo_result" not in st.session_state:
        st.session_state["is_demo_result"] = True

    # When scenario selection changes in Demo Mode, update requirements and report
    scenario_changed = (
        selected_scenario_key is not None
        and st.session_state["current_scenario"] != selected_scenario_key
    )

    out_dir = _REPO_ROOT / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    if scenario_changed and selected_scenario_key and demo_mode:
        st.session_state["current_scenario"] = selected_scenario_key
        scenario_data = scenarios[selected_scenario_key]

        # Extract representative description from requirement JSON
        req_obj = scenario_data["req"]
        app_type = req_obj.get("app_type", "web application")
        users = req_obj.get("expected_users", "100,000")
        pattern = scenario_data["arch"].get("pattern", "reference pattern")
        st.session_state["req_text"] = (
            f"Highly available {app_type} supporting ~{users:,} users with steady traffic, "
            f"relational storage, and automated failover ({pattern})."
            if isinstance(users, (int, float))
            else f"Highly available {app_type} supporting {users} users ({pattern})."
        )

        # Generate report for selected scenario using local deterministic pipeline
        try:
            report = run_downstream(scenario_data["req"], scenario_data["arch"], out_dir)
            st.session_state["report"] = report
            st.session_state["is_demo_result"] = True
        except Exception as err:
            st.error(f"Error computing report for scenario '{selected_scenario_key}': {err}")

    # -------------------------------------------------------------------------
    # Main Input & Action Area
    # -------------------------------------------------------------------------
    st.subheader("Architecture Requirements")

    input_text = st.text_area(
        "Enter natural language application requirements:",
        value=st.session_state["req_text"],
        height=110,
        placeholder="e.g. Build a scalable e-commerce website with 100k users, high availability, and relational database.",
        key="requirement_input_box",
    )

    col_btn, col_mode_info = st.columns([1, 4])
    with col_btn:
        generate_clicked = st.button("Generate", type="primary", use_container_width=True)

    with col_mode_info:
        if demo_mode:
            st.info(
                "💡 **Demo Mode Active:** Running locally with verified reference scenario. "
                "No AWS credentials or internet access required."
            )
        else:
            st.warning(
                "🌐 **Live Mode:** Natural-language parsing requires Amazon Bedrock credentials "
                "configured in region `ap-south-1`."
            )

    # -------------------------------------------------------------------------
    # Generate Trigger Handling
    # -------------------------------------------------------------------------
    if generate_clicked:
        stripped_input = input_text.strip()
        if not stripped_input:
            st.error("Please enter architecture requirements before generating.")
        elif demo_mode:
            # In Demo mode, execute the local mock pipeline
            if selected_scenario_key and selected_scenario_key in scenarios:
                scenario_data = scenarios[selected_scenario_key]
                with st.spinner("Generating architecture recommendation (Demo mode)..."):
                    try:
                        report = run_downstream(scenario_data["req"], scenario_data["arch"], out_dir)
                        st.session_state["report"] = report
                        st.session_state["req_text"] = stripped_input
                        st.session_state["is_demo_result"] = True
                        st.success(f"Demonstration report updated for '{scenario_data['title']}'.")
                    except Exception as exc:
                        st.error(f"Pipeline error in Demo mode: {exc}")
            else:
                st.error("No valid demonstration scenario available to run.")
        else:
            # Live Mode execution using run_full
            with st.spinner("Analyzing requirements with Amazon Bedrock and assembling architecture..."):
                try:
                    report = run_full(stripped_input, out_dir)
                    st.session_state["report"] = report
                    st.session_state["req_text"] = stripped_input
                    st.session_state["is_demo_result"] = False
                    st.success("Architecture generated successfully via live pipeline!")
                except Exception as live_err:
                    err_msg = str(live_err)
                    st.error(
                        "**Live architecture generation failed.**\n\n"
                        "Live mode requires active AWS Bedrock configuration:\n"
                        "- AWS credentials (`aws configure`) with Bedrock permissions in `ap-south-1`.\n"
                        "- A valid Foundation Model ID configured in `src/aws_arch/llm.py`.\n\n"
                        f"*Details:* `{err_msg}`\n\n"
                        "💡 **Recommendation:** Enable **Demo mode** in the sidebar to demonstrate the pipeline offline without AWS credentials."
                    )

    # -------------------------------------------------------------------------
    # Result Presentation (Tabs)
    # -------------------------------------------------------------------------
    current_report = st.session_state.get("report")

    if not current_report:
        st.info("Select a scenario or enter requirements above and click **Generate** to inspect the architecture.")
        return

    st.markdown("---")

    # Display scenario indicator banner
    if st.session_state.get("is_demo_result"):
        current_title = (
            scenarios[st.session_state["current_scenario"]]["title"]
            if st.session_state.get("current_scenario") in scenarios
            else "Reference Scenario"
        )
        st.markdown(f"### Results: {current_title}")
        st.caption("Demonstration output generated by the deterministic downstream pipeline.")
    else:
        st.markdown("### Results: Live Pipeline Recommendation")

    tab_services, tab_diagram, tab_cost, tab_security, tab_json = st.tabs(
        ["📦 Services", "🗺️ Diagram", "💰 Cost", "🛡️ Security", "📄 Raw JSON"]
    )

    # -------------------------------------------------------------------------
    # Tab 1: Services
    # -------------------------------------------------------------------------
    with tab_services:
        services = current_report.get("services", [])
        if services:
            st.subheader(f"Recommended Services ({len(services)})")
            for svc in services:
                svc_type = svc.get("type", "Unknown Service")
                role = svc.get("role", "Application Component")
                rationale = svc.get("why", "Standard Well-Architected component.")
                category = catalogue.get(svc_type, {}).get("category", "infrastructure").title()

                with st.expander(f"**{svc_type}** — *{role.title()}* (`{category}`)", expanded=True):
                    st.markdown(f"**Role:** {role}")
                    st.markdown(f"**Category:** `{category}`")
                    st.markdown(f"**Architectural Rationale:** {rationale}")
        else:
            st.warning("No services listed in the current architecture report.")

    # -------------------------------------------------------------------------
    # Tab 2: Diagram (Resilient Fallback: PNG -> Graphviz -> DOT Code)
    # -------------------------------------------------------------------------
    with tab_diagram:
        st.subheader("Architecture Topology")

        diagram_files = current_report.get("diagram_files", [])
        png_path = None
        dot_path = None

        # Check declared diagram files and output directory
        for f in diagram_files:
            p = Path(f)
            if p.suffix == ".png" and p.exists():
                png_path = p
            elif p.suffix == ".dot" and p.exists():
                dot_path = p

        # Fallback to output directory if not in diagram_files list
        if not png_path and (out_dir / "diagram.png").exists():
            png_path = out_dir / "diagram.png"
        if not dot_path and (out_dir / "diagram.dot").exists():
            dot_path = out_dir / "diagram.dot"

        rendered_visual = False

        # 1. Render PNG if present
        if png_path and png_path.exists() and png_path.stat().st_size > 0:
            try:
                st.image(str(png_path), caption="Generated Architecture Topology", use_container_width=True)
                rendered_visual = True
            except Exception:
                rendered_visual = False

        # 2. Render DOT via Streamlit's Graphviz component if PNG unavailable
        dot_content = None
        if dot_path and dot_path.exists():
            try:
                dot_content = dot_path.read_text(encoding="utf-8")
            except Exception:
                dot_content = None

        if not rendered_visual and dot_content:
            try:
                st.graphviz_chart(dot_content)
                st.caption("Rendered in-browser from Graphviz DOT source.")
                rendered_visual = True
            except Exception as gv_err:
                st.warning(f"Could not render Graphviz visualization in browser: {gv_err}")

        # 3. Always provide DOT source inspection
        if dot_content:
            with st.expander("View Graphviz DOT Source Code", expanded=not rendered_visual):
                st.code(dot_content, language="dot")
        elif not rendered_visual:
            st.warning(
                "No diagram output file was found. Diagram rendering requires the Graphviz `dot` "
                "executable on system PATH for PNG generation."
            )

    # -------------------------------------------------------------------------
    # Tab 3: Cost
    # -------------------------------------------------------------------------
    with tab_cost:
        st.subheader("Estimated Cost Projections")
        cost_data = current_report.get("cost", {})

        low_val = cost_data.get("monthly_usd_low")
        high_val = cost_data.get("monthly_usd_high")
        region = cost_data.get("region", "ap-south-1")
        checked_on = cost_data.get("prices_checked_on", "TODO")
        status = cost_data.get("status", "complete")
        note = cost_data.get("note", "Order-of-magnitude estimate; verify against official AWS pricing.")

        # Metric summary cards
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(
                "Monthly Estimate (Low)",
                f"${float(low_val):,.2f}" if low_val is not None else "Incomplete",
            )
        with c2:
            st.metric(
                "Monthly Estimate (High)",
                f"${float(high_val):,.2f}" if high_val is not None else "Incomplete",
            )
        with c3:
            st.metric("Region", region.upper(), help="Pricing evaluated for Asia Pacific (Mumbai)")

        st.caption(f"ℹ️ **Note:** {note} *(Prices checked: {checked_on})*")

        if status == "incomplete":
            st.warning("⚠️ Pricing for one or more services is unverified or incomplete.")

        # Per-service breakdown table if available
        breakdown = cost_data.get("breakdown")
        if breakdown and isinstance(breakdown, dict):
            st.markdown("#### Per-Service Cost Breakdown")
            table_rows = []
            for item_id, item in breakdown.items():
                table_rows.append({
                    "Component": item_id,
                    "Service": item.get("service", item_id),
                    "Low (USD)": f"${float(item.get('monthly_usd_low', 0)):,.2f}" if item.get('monthly_usd_low') is not None else "N/A",
                    "High (USD)": f"${float(item.get('monthly_usd_high', 0)):,.2f}" if item.get('monthly_usd_high') is not None else "N/A",
                    "Usage Assumption": item.get("usage_assumption", "Standard workload"),
                })
            st.dataframe(table_rows, use_container_width=True)

        # Assumptions list
        assumptions = current_report.get("assumptions", [])
        if assumptions:
            with st.expander("Usage & Sizing Assumptions", expanded=False):
                for a in assumptions:
                    st.markdown(f"- {a}")

    # -------------------------------------------------------------------------
    # Tab 4: Security
    # -------------------------------------------------------------------------
    with tab_security:
        st.subheader("Well-Architected Review Findings")
        findings = current_report.get("security", [])

        if not findings:
            st.info("No security or reliability findings returned for this architecture.")
        else:
            # Summary metrics
            passed_count = sum(1 for f in findings if f.get("passed"))
            failed_count = len(findings) - passed_count

            s1, s2, s3 = st.columns(3)
            with s1:
                st.metric("Total Checks", len(findings))
            with s2:
                st.metric("Passed", passed_count)
            with s3:
                st.metric("Needs Attention", failed_count)

            # Group findings by pillar
            pillars: dict[str, list[dict[str, Any]]] = {}
            for f in findings:
                p_name = f.get("pillar", "General Security")
                pillars.setdefault(p_name, []).append(f)

            for pillar_name, p_findings in pillars.items():
                st.markdown(f"#### {pillar_name} Pillar")
                for item in p_findings:
                    rule = item.get("rule", "Security Rule")
                    is_ok = item.get("passed", False)
                    rec = item.get("recommendation")
                    finding_id = item.get("id")
                    severity = item.get("severity")

                    prefix = f"[{finding_id}] " if finding_id else ""
                    badge = "✅ **PASS**" if is_ok else "⚠️ **NEEDS ATTENTION**"
                    sev_str = f" | Severity: `{severity.upper()}`" if severity else ""

                    with st.expander(f"{badge}: {prefix}{rule}{sev_str}", expanded=not is_ok):
                        st.markdown(f"**Pillar:** `{pillar_name}`")
                        st.markdown(f"**Rule Description:** {rule}")
                        if is_ok:
                            st.success("Complies with Well-Architected recommendation.")
                        else:
                            st.warning(f"**Remediation Recommendation:** {rec}")

    # -------------------------------------------------------------------------
    # Tab 5: Raw JSON
    # -------------------------------------------------------------------------
    with tab_json:
        st.subheader("Raw Architecture Report JSON")
        st.caption("Inspect the exact deterministic output dictionary generated by the pipeline.")

        clean_report_json = json.dumps(current_report, indent=2)
        st.json(current_report)

        st.download_button(
            label="Download Report JSON",
            data=clean_report_json,
            file_name="architecture_recommendation.json",
            mime="application/json",
            key="download_report_button",
        )


if __name__ == "__main__":
    main()
