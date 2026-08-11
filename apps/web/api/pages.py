# Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from apps.web.core.dependencies import get_db, get_current_user
from cura_frame import Candidate
from cura_frame.bundles import get_available_bundles
from cura_frame.cli import evaluate_candidate
from cura_frame.db import execute

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_properties(**kwargs: Optional[float]) -> dict[str, float]:
    return {key: value for key, value in kwargs.items() if value is not None}


@router.get("/", response_class=HTMLResponse)
def home(session: Optional[str] = Cookie(default=None), user: Optional[str] = Depends(get_current_user)):
    if user:
        return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user: Optional[str] = Depends(get_current_user)):
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(request, "dashboard.html", {"user": user})


@router.get("/calculator", response_class=HTMLResponse)
def calculator_get(request: Request, user: Optional[str] = Depends(get_current_user)):
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "calculator.html",
        {
            "user": user,
            "result": None,
            "error": None,
            "bundles": get_available_bundles(),
        },
    )


@router.post("/calculator", response_class=HTMLResponse)
def calculator_post(
    request: Request,
    session: Optional[str] = Cookie(default=None),
    user: Optional[str] = Depends(get_current_user),
    logP: Optional[float] = Form(default=None),
    hERG_IC50: Optional[float] = Form(default=None),
    beta1_selectivity: Optional[float] = Form(default=None),
    molecular_weight: Optional[float] = Form(default=None),
    polar_surface_area: Optional[float] = Form(default=None),
    hydrogen_bond_donors: Optional[float] = Form(default=None),
    hydrogen_bond_acceptors: Optional[float] = Form(default=None),
    Kd_5HT1A: Optional[float] = Form(default=None),
    Kd_5HT2A: Optional[float] = Form(default=None),
    Kd_D2: Optional[float] = Form(default=None),
    plasma_half_life: Optional[float] = Form(default=None),
    bundle: str = Form(default="core-safety"),
):
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

    templates: Jinja2Templates = request.app.state.templates
    values = {
        "logP": logP,
        "hERG_IC50": hERG_IC50,
        "beta1_selectivity": beta1_selectivity,
        "molecular_weight": molecular_weight,
        "polar_surface_area": polar_surface_area,
        "hydrogen_bond_donors": hydrogen_bond_donors,
        "hydrogen_bond_acceptors": hydrogen_bond_acceptors,
        "Kd_5HT1A": Kd_5HT1A,
        "Kd_5HT2A": Kd_5HT2A,
        "Kd_D2": Kd_D2,
        "plasma_half_life": plasma_half_life,
        "bundle": bundle,
        "bundles": get_available_bundles(),
    }
    properties = _build_properties(
        logP=logP,
        hERG_IC50=hERG_IC50,
        beta1_selectivity=beta1_selectivity,
        molecular_weight=molecular_weight,
        polar_surface_area=polar_surface_area,
        hydrogen_bond_donors=hydrogen_bond_donors,
        hydrogen_bond_acceptors=hydrogen_bond_acceptors,
        Kd_5HT1A=Kd_5HT1A,
        Kd_5HT2A=Kd_5HT2A,
        Kd_D2=Kd_D2,
        plasma_half_life=plasma_half_life,
    )

    try:
        candidate = Candidate(name="web_calculator", properties=properties)
        result = evaluate_candidate(candidate, bundle_name=bundle, population=None, strict=False)
    except (TypeError, ValueError):
        return templates.TemplateResponse(
            request,
            "calculator.html",
            {"user": user, "result": None, "error": "Invalid input provided.", **values},
        )
    except Exception:
        logger.exception("Unexpected calculator evaluation failure for user=%s bundle=%s", user, bundle)
        return templates.TemplateResponse(
            request,
            "calculator.html",
            {"user": user, "result": None, "error": "An internal system error occurred.", **values},
        )

    return templates.TemplateResponse(
        request,
        "calculator.html",
        {"user": user, "result": result, "error": None, **values},
    )


@router.get("/form", response_class=HTMLResponse)
def form_get(request: Request, user: Optional[str] = Depends(get_current_user)):
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "form.html",
        {"user": user, "results": None, "error": None, "bundles": get_available_bundles()},
    )


@router.post("/form", response_class=HTMLResponse)
def form_post(
    request: Request,
    db=Depends(get_db),
    user: Optional[str] = Depends(get_current_user),
    logP: Optional[float] = Form(default=None),
    hERG_IC50: Optional[float] = Form(default=None),
    beta1_selectivity: Optional[float] = Form(default=None),
    molecular_weight: Optional[float] = Form(default=None),
    polar_surface_area: Optional[float] = Form(default=None),
    hydrogen_bond_donors: Optional[float] = Form(default=None),
    hydrogen_bond_acceptors: Optional[float] = Form(default=None),
    Kd_5HT1A: Optional[float] = Form(default=None),
    Kd_5HT2A: Optional[float] = Form(default=None),
    Kd_D2: Optional[float] = Form(default=None),
    plasma_half_life: Optional[float] = Form(default=None),
):
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

    templates: Jinja2Templates = request.app.state.templates
    values = _build_properties(
        logP=logP,
        hERG_IC50=hERG_IC50,
        beta1_selectivity=beta1_selectivity,
        molecular_weight=molecular_weight,
        polar_surface_area=polar_surface_area,
        hydrogen_bond_donors=hydrogen_bond_donors,
        hydrogen_bond_acceptors=hydrogen_bond_acceptors,
        Kd_5HT1A=Kd_5HT1A,
        Kd_5HT2A=Kd_5HT2A,
        Kd_D2=Kd_D2,
        plasma_half_life=plasma_half_life,
    )

    try:
        candidate = Candidate(name="form_all_tests", properties=values)
        results = []
        for bundle_key, bundle_label in get_available_bundles():
            result = evaluate_candidate(candidate, bundle_name=bundle_key, population=None, strict=False)
            results.append({"bundle": bundle_key, "label": bundle_label, "status": result.status.value, "violations": result.violations})
    except (TypeError, ValueError):
        return templates.TemplateResponse(
            request,
            "form.html",
            {"user": user, "results": None, "error": "Invalid input provided.", "values": values},
        )
    except Exception:
        logger.exception("Unexpected form evaluation failure for user=%s", user)
        return templates.TemplateResponse(
            request,
            "form.html",
            {"user": user, "results": None, "error": "An internal system error occurred.", "values": values},
        )

    results_json = json.dumps([
        {
            "bundle": row["bundle"],
            "label": row["label"],
            "status": row["status"],
            "violations": [
                {
                    "constraint": violation.constraint,
                    "observed": violation.observed,
                    "threshold": violation.threshold,
                    "severity": violation.severity.value,
                }
                for violation in row["violations"]
            ],
        }
        for row in results
    ])
    execute(
        db,
        request.app.state.db_path,
        """
        INSERT INTO form_submissions (
            username, timestamp,
            logP, hERG_IC50, beta1_selectivity,
            molecular_weight, polar_surface_area,
            hydrogen_bond_donors, hydrogen_bond_acceptors,
            Kd_5HT1A, Kd_5HT2A, Kd_D2, plasma_half_life,
            results_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user,
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            logP, hERG_IC50, beta1_selectivity,
            molecular_weight, polar_surface_area,
            hydrogen_bond_donors, hydrogen_bond_acceptors,
            Kd_5HT1A, Kd_5HT2A, Kd_D2, plasma_half_life,
            results_json,
        ),
    )
    db.commit()
    return templates.TemplateResponse(request, "form.html", {"user": user, "results": results, "error": None, "values": values})


@router.get("/sweep", response_class=HTMLResponse)
def sweep_get(request: Request, user: Optional[str] = Depends(get_current_user)):
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "sweep.html",
        {
            "user": user,
            "results": None,
            "inflections": None,
            "bundles": get_available_bundles(),
        }
    )


@router.post("/sweep", response_class=HTMLResponse)
def sweep_post(
    request: Request,
    user: Optional[str] = Depends(get_current_user),
    logP: Optional[float] = Form(default=2.0),
    hERG_IC50: Optional[float] = Form(default=15.0),
    beta1_selectivity: Optional[float] = Form(default=120.0),
    molecular_weight: Optional[float] = Form(default=450.0),
    polar_surface_area: Optional[float] = Form(default=75.0),
    plasma_half_life: Optional[float] = Form(default=12.0),
    sweep_prop: str = Form(default="logP"),
    sweep_min: float = Form(default=0.0),
    sweep_max: float = Form(default=10.0),
    sweep_steps: int = Form(default=15),
    bundle: str = Form(default="core-safety"),
    population: str = Form(default="None"),
):
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

    templates: Jinja2Templates = request.app.state.templates

    # Map population string
    pop_arg = None if population == "None" else population

    # Collect properties
    properties = _build_properties(
        logP=logP,
        hERG_IC50=hERG_IC50,
        beta1_selectivity=beta1_selectivity,
        molecular_weight=molecular_weight,
        polar_surface_area=polar_surface_area,
        plasma_half_life=plasma_half_life,
    )

    # Store form values to pass back to the template
    values = {
        "logP": logP,
        "hERG_IC50": hERG_IC50,
        "beta1_selectivity": beta1_selectivity,
        "molecular_weight": molecular_weight,
        "polar_surface_area": polar_surface_area,
        "plasma_half_life": plasma_half_life,
        "sweep_prop": sweep_prop,
        "sweep_min": sweep_min,
        "sweep_max": sweep_max,
        "sweep_steps": sweep_steps,
        "bundle": bundle,
        "population": population,
        "bundles": get_available_bundles(),
    }

    try:
        from cura_frame import CuraFrame, Candidate
        from cura_frame.cli import resolve_bundle
        from cura_frame.sensitivity import run_1d_sweep, find_inflection_points

        # Build framework
        constraints = resolve_bundle(bundle)
        cura = CuraFrame(constraints, name=f"CuraFrame_Web_{bundle}")

        # Register standard population modifiers if needed
        POPULATION_MODIFIERS = {
            "elderly": {
                "hERG_IC50": lambda c: c.threshold * 1.5,
            },
            "asthmatic": {
                "beta1_selectivity": lambda c: c.threshold * 2.0,
            },
            "pediatric": {
                "hERG_IC50": lambda c: c.threshold * 1.3,
                "molecular_weight": lambda c: (c.threshold[0], c.threshold[1] * 0.9),
            }
        }
        if pop_arg and pop_arg in POPULATION_MODIFIERS:
            cura.add_population(pop_arg, POPULATION_MODIFIERS[pop_arg])

        candidate = Candidate(name="web_sweep_baseline", properties=properties)

        results = run_1d_sweep(
            framework=cura,
            baseline_candidate=candidate,
            property_name=sweep_prop,
            min_val=sweep_min,
            max_val=sweep_max,
            steps=sweep_steps,
            population=pop_arg,
            strict=False  # Keep strict False to allow missing fields like non-sweep ones
        )

        inflections = find_inflection_points(results)

        return templates.TemplateResponse(
            request,
            "sweep.html",
            {
                "user": user,
                "results": results,
                "inflections": inflections,
                "error": None,
                **values,
            }
        )

    except Exception as e:
        logger.exception("Unexpected sweep execution failure for user=%s", user)
        return templates.TemplateResponse(
            request,
            "sweep.html",
            {
                "user": user,
                "results": None,
                "inflections": None,
                "error": f"An error occurred: {str(e)}",
                **values,
            }
        )
