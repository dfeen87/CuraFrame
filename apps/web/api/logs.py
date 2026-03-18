from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from apps.web.core.dependencies import get_current_user, get_db
from cura_frame.db import execute, fetchall, is_postgres

router = APIRouter()


@router.post("/logs/record", response_class=HTMLResponse)
def logs_record(
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
    bundle: str = Form(default="core-safety"),
    status_val: str = Form(default=""),
):
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    execute(
        db,
        request.app.state.db_path,
        """
        INSERT INTO logs (
            username, timestamp,
            logP, hERG_IC50, beta1_selectivity,
            molecular_weight, polar_surface_area,
            hydrogen_bond_donors, hydrogen_bond_acceptors,
            Kd_5HT1A, Kd_5HT2A, Kd_D2, plasma_half_life,
            bundle, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user,
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            logP, hERG_IC50, beta1_selectivity,
            molecular_weight, polar_surface_area,
            hydrogen_bond_donors, hydrogen_bond_acceptors,
            Kd_5HT1A, Kd_5HT2A, Kd_D2, plasma_half_life,
            bundle, status_val,
        ),
    )
    db.commit()
    return RedirectResponse("/logs", status_code=status.HTTP_302_FOUND)


@router.get("/logs", response_class=HTMLResponse)
def logs_get(request: Request, db=Depends(get_db), user: Optional[str] = Depends(get_current_user)):
    if not user:
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    rows = fetchall(
        db,
        request.app.state.db_path,
        """
        SELECT id, timestamp,
               logP, hERG_IC50, beta1_selectivity,
               molecular_weight, polar_surface_area,
               hydrogen_bond_donors, hydrogen_bond_acceptors,
               Kd_5HT1A, Kd_5HT2A, Kd_D2, plasma_half_life,
               bundle, status
        FROM logs
        WHERE username = ?
        ORDER BY id DESC
        """,
        (user,),
    )
    logs = rows if is_postgres(request.app.state.db_path) else [dict(row) for row in rows]
    return request.app.state.templates.TemplateResponse(request, "logs.html", {"user": user, "logs": logs})
