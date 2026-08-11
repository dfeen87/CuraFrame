# Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
from __future__ import annotations

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[str] = mapped_column(String, nullable=False)
    logP: Mapped[float | None] = mapped_column(Float)
    hERG_IC50: Mapped[float | None] = mapped_column(Float)
    beta1_selectivity: Mapped[float | None] = mapped_column(Float)
    molecular_weight: Mapped[float | None] = mapped_column(Float)
    polar_surface_area: Mapped[float | None] = mapped_column(Float)
    hydrogen_bond_donors: Mapped[float | None] = mapped_column(Float)
    hydrogen_bond_acceptors: Mapped[float | None] = mapped_column(Float)
    Kd_5HT1A: Mapped[float | None] = mapped_column(Float)
    Kd_5HT2A: Mapped[float | None] = mapped_column(Float)
    Kd_D2: Mapped[float | None] = mapped_column(Float)
    plasma_half_life: Mapped[float | None] = mapped_column(Float)
    bundle: Mapped[str | None] = mapped_column(String)
    status: Mapped[str | None] = mapped_column(String)


class FormSubmission(Base):
    __tablename__ = "form_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[str] = mapped_column(String, nullable=False)
    logP: Mapped[float | None] = mapped_column(Float)
    hERG_IC50: Mapped[float | None] = mapped_column(Float)
    beta1_selectivity: Mapped[float | None] = mapped_column(Float)
    molecular_weight: Mapped[float | None] = mapped_column(Float)
    polar_surface_area: Mapped[float | None] = mapped_column(Float)
    hydrogen_bond_donors: Mapped[float | None] = mapped_column(Float)
    hydrogen_bond_acceptors: Mapped[float | None] = mapped_column(Float)
    Kd_5HT1A: Mapped[float | None] = mapped_column(Float)
    Kd_5HT2A: Mapped[float | None] = mapped_column(Float)
    Kd_D2: Mapped[float | None] = mapped_column(Float)
    plasma_half_life: Mapped[float | None] = mapped_column(Float)
    results_json: Mapped[str | None] = mapped_column(Text)
