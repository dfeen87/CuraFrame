from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from fastapi import Request

from cura_frame.db import execute, get_connection, is_postgres

from apps.web.core.config import WebConfig

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker
except ImportError:  # pragma: no cover
    create_engine = None

    class Session:  # type: ignore[override]
        pass

    class _SessionFactory:
        def configure(self, **kwargs):
            return None

        def __call__(self):
            class _SessionContext:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

            return _SessionContext()

    def sessionmaker(*args, **kwargs):  # type: ignore[misc]
        return _SessionFactory()

try:
    from psycopg_pool import ConnectionPool
except ImportError:  # pragma: no cover
    ConnectionPool = None

logger = logging.getLogger(__name__)

SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def init_db(db_path: str) -> None:
    conn = get_connection(db_path)
    try:
        if is_postgres(db_path):
            user_id = "BIGSERIAL PRIMARY KEY"
            num_type = "DOUBLE PRECISION"
        else:
            user_id = "INTEGER PRIMARY KEY AUTOINCREMENT"
            num_type = "REAL"
        execute(
            conn,
            db_path,
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id {user_id},
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            """,
        )
        execute(
            conn,
            db_path,
            f"""
            CREATE TABLE IF NOT EXISTS logs (
                id {user_id},
                username TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                logP {num_type},
                hERG_IC50 {num_type},
                beta1_selectivity {num_type},
                molecular_weight {num_type},
                polar_surface_area {num_type},
                hydrogen_bond_donors {num_type},
                hydrogen_bond_acceptors {num_type},
                Kd_5HT1A {num_type},
                Kd_5HT2A {num_type},
                Kd_D2 {num_type},
                plasma_half_life {num_type},
                bundle TEXT,
                status TEXT
            )
            """,
        )
        execute(
            conn,
            db_path,
            f"""
            CREATE TABLE IF NOT EXISTS form_submissions (
                id {user_id},
                username TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                logP {num_type},
                hERG_IC50 {num_type},
                beta1_selectivity {num_type},
                molecular_weight {num_type},
                polar_surface_area {num_type},
                hydrogen_bond_donors {num_type},
                hydrogen_bond_acceptors {num_type},
                Kd_5HT1A {num_type},
                Kd_5HT2A {num_type},
                Kd_D2 {num_type},
                plasma_half_life {num_type},
                results_json TEXT
            )
            """,
        )
        conn.commit()
    finally:
        conn.close()


def configure_database(app, config: WebConfig) -> None:
    db_path = config.db_path
    app.state.db_path = db_path
    app.state.db_pool = None

    if is_postgres(db_path):
        if ConnectionPool is None:
            raise RuntimeError(
                "PostgreSQL pooling requested but psycopg_pool is not installed."
            )
        app.state.db_pool = ConnectionPool(conninfo=db_path, open=True)
        sqlalchemy_url = db_path
    else:
        sqlalchemy_url = f"sqlite:///{db_path}"

    if create_engine is not None:
        engine = create_engine(sqlalchemy_url, future=True)
        SessionLocal.configure(bind=engine)
        app.state.db_engine = engine
    else:
        app.state.db_engine = None
    logger.info("Configured database for %s", db_path)


def close_database(app) -> None:
    pool = getattr(app.state, "db_pool", None)
    if pool is not None:
        pool.close()
    engine = getattr(app.state, "db_engine", None)
    if engine is not None:
        engine.dispose()


@contextmanager
def _connection_context(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    db_path = request.app.state.db_path
    if pool is not None:
        with pool.connection() as conn:
            yield conn
    else:
        conn = get_connection(db_path)
        try:
            yield conn
        finally:
            conn.close()


def get_db(request: Request):
    with _connection_context(request) as conn:
        yield conn


def get_db_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
