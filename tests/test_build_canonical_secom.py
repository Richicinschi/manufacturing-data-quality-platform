"""Tests for building the canonical SECOM table."""

import pandas as pd
import pytest
from sqlalchemy import text

from src.db.connection import get_engine
from src.etl.build_canonical_secom import build_canonical_secom


@pytest.fixture
def engine():
    return get_engine()


def test_build_canonical_secom_creates_table(engine):
    row_count = build_canonical_secom(
        source_schema="raw",
        target_schema="raw",
        target_table="secom_canonical_test",
    )
    assert row_count == 1567

    # Verify table exists and has correct shape
    dialect = engine.dialect.name
    table_ref = "raw.secom_canonical_test" if dialect != "sqlite" else "secom_canonical_test"
    df = pd.read_sql(f"SELECT * FROM {table_ref}", engine)
    assert len(df) == 1567
    assert "entity_id" in df.columns
    assert "test_timestamp" in df.columns
    assert "yield_label" in df.columns
    assert "pass_fail" in df.columns
    assert "feature_001" in df.columns
    assert "feature_590" in df.columns


def test_canonical_pass_fail_consistency(engine):
    dialect = engine.dialect.name
    table_ref = "raw.secom_canonical_test" if dialect != "sqlite" else "secom_canonical_test"
    df = pd.read_sql(f"SELECT * FROM {table_ref}", engine)

    pass_mask = df["yield_label"] == -1
    fail_mask = df["yield_label"] == 1
    assert df.loc[pass_mask, "pass_fail"].eq("pass").all()
    assert df.loc[fail_mask, "pass_fail"].eq("fail").all()


def test_canonical_ordered_by_timestamp(engine):
    dialect = engine.dialect.name
    table_ref = "raw.secom_canonical_test" if dialect != "sqlite" else "secom_canonical_test"
    df = pd.read_sql(f"SELECT * FROM {table_ref}", engine)
    timestamps = pd.to_datetime(df["test_timestamp"])
    assert timestamps.is_monotonic_increasing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
