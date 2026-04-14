"""Tests for SECOM join and entity builder."""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import text

from src.db.connection import get_engine
from src.etl.raw_ingest import ingest_secom
from src.etl.secom_join import build_secom_entities, save_secom_entities


@pytest.fixture(scope="session")
def db_connection_string():
    """Provide a SQLite file connection string for isolated test data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    yield f"sqlite:///{tmp_path}"
    try:
        os.unlink(tmp_path)
    except PermissionError:
        pass  # Windows may keep the file locked briefly


@pytest.fixture
def engine(db_connection_string):
    """Provide a SQLAlchemy engine using the test database."""
    return get_engine(db_connection_string)


@pytest.fixture
def raw_schema() -> str:
    """Default raw schema name."""
    return "raw"


@pytest.fixture(autouse=True)
def load_raw_data(engine, raw_schema, db_connection_string):
    """Ingest raw SECOM data so join tests have source tables to query."""
    data_dir = Path(__file__).resolve().parent.parent / "data" / "raw" / "secom"
    ingest_secom(
        data_path=data_dir / "secom.data",
        labels_path=data_dir / "secom_labels.data",
        schema=raw_schema,
        connection_string=db_connection_string,
    )


def test_build_secom_entities_shape(engine, raw_schema, db_connection_string):
    """Verify the joined DataFrame has the expected shape and columns."""
    df = build_secom_entities(schema=raw_schema, connection_string=db_connection_string)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1567, "Expected 1,567 SECOM entities"
    assert "entity_id" in df.columns
    assert "yield_label" in df.columns
    assert "test_timestamp" in df.columns
    assert "pass_fail" in df.columns
    assert "feature_001" in df.columns
    assert "feature_590" in df.columns


def test_build_secom_entities_timestamp_order(engine, raw_schema, db_connection_string):
    """Verify rows are ordered by test_timestamp."""
    df = build_secom_entities(schema=raw_schema, connection_string=db_connection_string)
    timestamps = pd.to_datetime(df["test_timestamp"])
    assert timestamps.is_monotonic_increasing


def test_build_secom_entities_pass_fail_mapping(engine, raw_schema, db_connection_string):
    """Verify pass/fail mapping is consistent with yield_label."""
    df = build_secom_entities(schema=raw_schema, connection_string=db_connection_string)

    pass_mask = df["yield_label"] == -1
    fail_mask = df["yield_label"] == 1

    assert df.loc[pass_mask, "pass_fail"].eq("pass").all()
    assert df.loc[fail_mask, "pass_fail"].eq("fail").all()


def test_save_secom_entities(engine, raw_schema, db_connection_string):
    """Verify persisting SECOM entities to staging works."""
    df = build_secom_entities(schema=raw_schema, connection_string=db_connection_string)
    rows_written = save_secom_entities(
        df,
        target_schema="staging",
        target_table="secom_entities_test",
        connection_string=db_connection_string,
    )

    assert rows_written == 1567

    # Read back and verify
    dialect = engine.dialect.name
    table_ref = (
        "staging.secom_entities_test"
        if dialect != "sqlite"
        else "secom_entities_test"
    )
    result = pd.read_sql(f"SELECT * FROM {table_ref}", engine)
    assert len(result) == 1567
    assert "test_timestamp" in result.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
