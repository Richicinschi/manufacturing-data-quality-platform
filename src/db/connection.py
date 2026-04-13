"""PostgreSQL / SQLite connection manager for the manufacturing data platform."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Load environment variables from .env if present
load_dotenv(Path(".env"))


def build_connection_string(
    user: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: str | None = None,
    database: str | None = None,
    driver: str | None = None,
) -> str:
    """Build a database connection string from parts or environment variables.

    Environment variables (prefixed with MDQP_):
        MDQP_DB_USER, MDQP_DB_PASSWORD, MDQP_DB_HOST, MDQP_DB_PORT,
        MDQP_DB_NAME, MDQP_DB_DRIVER

    Falls back to plain DB_* variables if MDQP_* are not set.
    Supported drivers: postgresql, postgresql+psycopg2, sqlite (default: postgresql)
    """
    driver = (
        driver
        or os.getenv("MDQP_DB_DRIVER")
        or os.getenv("DB_DRIVER")
        or "postgresql+psycopg2"
    ).lower()

    if driver in ("sqlite", "sqlite3"):
        db_path = database or os.getenv("MDQP_DB_NAME") or os.getenv("DB_NAME") or "manufacturing_dw.db"
        return f"sqlite:///{db_path}"

    user = user or os.getenv("MDQP_DB_USER") or os.getenv("DB_USER") or "postgres"
    password = password or os.getenv("MDQP_DB_PASSWORD") or os.getenv("DB_PASSWORD") or "postgres"
    host = host or os.getenv("MDQP_DB_HOST") or os.getenv("DB_HOST") or "localhost"
    port = port or os.getenv("MDQP_DB_PORT") or os.getenv("DB_PORT") or "5432"
    database = database or os.getenv("MDQP_DB_NAME") or os.getenv("DB_NAME") or "manufacturing_dw"

    if "+" not in driver:
        driver = "postgresql+psycopg2"

    return f"{driver}://{user}:{password}@{host}:{port}/{database}"


def get_engine(connection_string: str | None = None) -> Engine:
    """Return a SQLAlchemy Engine.

    Args:
        connection_string: Optional explicit connection string.
            If omitted, one is built from environment variables.
    """
    conn_str = connection_string or build_connection_string()
    return create_engine(conn_str, pool_pre_ping=True)


def get_session(connection_string: str | None = None) -> Session:
    """Return a new SQLAlchemy Session bound to the engine.

    Args:
        connection_string: Optional explicit connection string.
    """
    engine = get_engine(connection_string)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def ensure_schema(engine: Engine, schema: str) -> None:
    """Create schema if it does not exist.

    For SQLite, schemas are emulated via ATTACH or ignored;
    this function simply ensures the main database is usable.
    """
    dialect = engine.dialect.name
    if dialect == "sqlite":
        return
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()
