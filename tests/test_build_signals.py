"""Tests for the long-format signal builder."""

from __future__ import annotations

import os
import tempfile

import pandas as pd
import pytest
from sqlalchemy import text

from src.db.connection import get_engine
from src.etl.build_signals import build_signal_values_long


@pytest.fixture(scope="session")
def db_connection_string():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    yield f"sqlite:///{tmp_path}"
    try:
        os.unlink(tmp_path)
    except PermissionError:
        pass


@pytest.fixture
def engine(db_connection_string):
    return get_engine(db_connection_string)


@pytest.fixture
def small_entity_table(engine):
    """Create a small test entity table in staging and return its name."""
    dialect = engine.dialect.name
    table_name = "secom_entities_signals_test"

    df = pd.DataFrame(
        {
            "entity_id": [1, 2, 3],
            "test_timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "yield_label": [-1, 1, -1],
            "pass_fail": ["pass", "fail", "pass"],
            "feature_x": [10.0, 20.0, None],
            "feature_y": [1.0, 2.0, 3.0],
        }
    )

    if dialect != "sqlite":
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            conn.commit()

    df.to_sql(
        table_name,
        con=engine,
        schema="staging" if dialect != "sqlite" else None,
        if_exists="replace",
        index=False,
    )
    return table_name


def test_build_signals_row_count(engine, small_entity_table, db_connection_string):
    row_count = build_signal_values_long(
        source_schema="staging",
        source_table=small_entity_table,
        target_schema="staging",
        target_table="signal_values_long_test",
        connection_string=db_connection_string,
    )

    entity_count = 3
    feature_count = 2  # feature_x, feature_y
    assert row_count == entity_count * feature_count


def test_build_signals_nulls_retained(engine, small_entity_table, db_connection_string):
    build_signal_values_long(
        source_schema="staging",
        source_table=small_entity_table,
        target_schema="staging",
        target_table="signal_values_long_test",
        connection_string=db_connection_string,
    )

    dialect = engine.dialect.name
    table_ref = (
        "staging.signal_values_long_test"
        if dialect != "sqlite"
        else "signal_values_long_test"
    )
    df = pd.read_sql(f"SELECT * FROM {table_ref}", engine)

    missing_rows = df[(df["feature_name"] == "feature_x") & (df["entity_id"] == 3)]
    assert len(missing_rows) == 1
    assert missing_rows.iloc[0]["is_missing"] == 1 or missing_rows.iloc[0]["is_missing"] == True
    assert pd.isna(missing_rows.iloc[0]["feature_value"])


def test_build_signals_every_entity_once_per_feature(engine, small_entity_table, db_connection_string):
    build_signal_values_long(
        source_schema="staging",
        source_table=small_entity_table,
        target_schema="staging",
        target_table="signal_values_long_test",
        connection_string=db_connection_string,
    )

    dialect = engine.dialect.name
    table_ref = (
        "staging.signal_values_long_test"
        if dialect != "sqlite"
        else "signal_values_long_test"
    )
    df = pd.read_sql(f"SELECT * FROM {table_ref}", engine)

    for feature in ["feature_x", "feature_y"]:
        feature_df = df[df["feature_name"] == feature]
        assert set(feature_df["entity_id"]) == {1, 2, 3}
        assert len(feature_df) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
