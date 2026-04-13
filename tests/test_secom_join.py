"""Tests for SECOM join and production entity builder."""

import os

import pandas as pd
import pytest
from sqlalchemy import text

from src.db.connection import get_engine
from src.etl.secom_join import build_production_entities, save_production_entities


@pytest.fixture
def engine():
    """Provide a SQLAlchemy engine using environment config."""
    return get_engine()


@pytest.fixture
def raw_schema() -> str:
    """Default raw schema name."""
    return "raw"


def test_build_production_entities_shape(engine, raw_schema):
    """Verify the joined DataFrame has the expected shape and columns."""
    df = build_production_entities(schema=raw_schema)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1567, "Expected 1,567 production entities"
    assert "entity_id" in df.columns
    assert "yield_label" in df.columns
    assert "test_timestamp" in df.columns
    assert "pass_fail" in df.columns
    assert "feature_001" in df.columns
    assert "feature_590" in df.columns


def test_build_production_entities_timestamp_order(engine, raw_schema):
    """Verify rows are ordered by test_timestamp."""
    df = build_production_entities(schema=raw_schema)
    timestamps = pd.to_datetime(df["test_timestamp"])
    assert timestamps.is_monotonic_increasing


def test_build_production_entities_pass_fail_mapping(engine, raw_schema):
    """Verify pass/fail mapping is consistent with yield_label."""
    df = build_production_entities(schema=raw_schema)

    pass_mask = df["yield_label"] == -1
    fail_mask = df["yield_label"] == 1

    assert df.loc[pass_mask, "pass_fail"].eq("pass").all()
    assert df.loc[fail_mask, "pass_fail"].eq("fail").all()


def test_save_production_entities(engine, raw_schema):
    """Verify persisting production entities to staging works."""
    df = build_production_entities(schema=raw_schema)
    rows_written = save_production_entities(
        df,
        target_schema="staging",
        target_table="production_entities_test",
    )

    assert rows_written == 1567

    # Read back and verify
    dialect = engine.dialect.name
    table_ref = (
        "staging.production_entities_test"
        if dialect != "sqlite"
        else "production_entities_test"
    )
    result = pd.read_sql(f"SELECT * FROM {table_ref}", engine)
    assert len(result) == 1567
    assert "test_timestamp" in result.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
