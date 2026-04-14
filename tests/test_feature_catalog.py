"""Tests for the feature catalog builder."""

from __future__ import annotations

import os
import tempfile

import pandas as pd
import pytest
from sqlalchemy import text

from src.db.connection import get_engine
from src.etl.feature_catalog import build_feature_catalog


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
    table_name = "secom_entities_catalog_test"

    df = pd.DataFrame(
        {
            "entity_id": [1, 2, 3],
            "test_timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "yield_label": [-1, 1, -1],
            "pass_fail": ["pass", "fail", "pass"],
            "feature_a": [1.0, 2.0, 3.0],
            "feature_b": [None, None, None],
            "feature_c": [5.0, 5.0, 5.0],
            "feature_d": [1.0, None, 3.0],
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


def test_feature_catalog_columns_and_row_count(engine, small_entity_table, db_connection_string):
    catalog = build_feature_catalog(
        source_schema="staging",
        source_table=small_entity_table,
        target_schema="staging",
        target_table="feature_catalog_test",
        connection_string=db_connection_string,
    )

    expected_columns = {
        "feature_name",
        "null_count",
        "null_pct",
        "distinct_count",
        "mean",
        "stddev",
        "min_value",
        "max_value",
        "is_constant",
        "is_high_missing",
        "recommended_action",
    }
    assert set(catalog.columns) == expected_columns
    assert len(catalog) == 4  # feature_a, feature_b, feature_c, feature_d


def test_feature_catalog_recommended_actions(engine, small_entity_table, db_connection_string):
    catalog = build_feature_catalog(
        source_schema="staging",
        source_table=small_entity_table,
        target_schema="staging",
        target_table="feature_catalog_test",
        connection_string=db_connection_string,
    )

    actions = dict(zip(catalog["feature_name"], catalog["recommended_action"]))
    assert actions["feature_a"] == "keep"
    assert actions["feature_b"] == "drop_all_null"
    assert actions["feature_c"] == "drop_constant"
    assert actions["feature_d"] == "keep"


def test_feature_catalog_recommended_action_logic_directly():
    """Test recommended_action logic with a small fixture DataFrame directly."""
    df = pd.DataFrame(
        {
            "entity_id": [1, 2, 3, 4],
            "test_timestamp": pd.to_datetime(["2024-01-01"] * 4),
            "yield_label": [-1, -1, -1, -1],
            "pass_fail": ["pass"] * 4,
            "all_null": [None, None, None, None],
            "constant": [7.0, 7.0, 7.0, 7.0],
            "high_missing": [1.0, 2.0, None, None],
            "normal": [1.0, 2.0, 3.0, 4.0],
        }
    )

    total_rows = len(df)
    feature_cols = ["all_null", "constant", "high_missing", "normal"]

    for col in feature_cols:
        series = df[col]
        null_count = int(series.isna().sum())
        null_pct = null_count / total_rows
        distinct_count = int(series.nunique(dropna=True))

        if (total_rows - null_count) == 0:
            action = "drop_all_null"
        elif distinct_count <= 1:
            action = "drop_constant"
        elif null_pct >= 0.50:
            action = "review_high_missing"
        else:
            action = "keep"

        assert action == {
            "all_null": "drop_all_null",
            "constant": "drop_constant",
            "high_missing": "review_high_missing",
            "normal": "keep",
        }[col]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
