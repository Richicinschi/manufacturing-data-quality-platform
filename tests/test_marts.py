"""Tests for the mart layer."""

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import text

from src.db.connection import get_engine
from src.etl.raw_ingest import ingest_secom
from src.etl.secom_join import build_secom_entities, save_secom_entities
from src.etl.feature_catalog import build_feature_catalog
from src.marts.overview import build_secom_overview
from src.marts.feature_missingness import build_feature_missingness
from src.marts.label_distribution import build_label_distribution
from src.marts.top_signal_fail_separation import build_top_signal_fail_separation
from src.marts.daily_yield_trend import build_daily_yield_trend
from src.marts.feature_action_summary import build_feature_action_summary
from src.marts.top_signal_profiles import build_top_signal_profiles
from src.marts.feature_failure_relationship import build_feature_failure_relationship
from src.marts.daily_failure_rollup import build_daily_failure_rollup
from src.marts.feature_priority_index import build_feature_priority_index


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
def source_schema() -> str:
    return "staging"


@pytest.fixture(autouse=True)
def load_staging_data(engine, source_schema, db_connection_string):
    """Ingest raw SECOM data and build staging tables for mart tests."""
    data_dir = Path(__file__).resolve().parent.parent / "data" / "raw" / "secom"
    ingest_secom(
        data_path=data_dir / "secom.data",
        labels_path=data_dir / "secom_labels.data",
        schema="raw",
        connection_string=db_connection_string,
    )
    df = build_secom_entities(schema="raw", connection_string=db_connection_string)
    save_secom_entities(
        df,
        target_schema=source_schema,
        target_table="secom_entities",
        connection_string=db_connection_string,
    )
    build_feature_catalog(
        source_schema=source_schema,
        source_table="secom_entities",
        target_schema=source_schema,
        target_table="feature_catalog",
        connection_string=db_connection_string,
    )


def test_secom_overview_reconciles_to_staging(engine, source_schema, db_connection_string):
    """mart.secom_overview counts reconcile to staging.secom_entities."""
    overview = build_secom_overview(
        source_schema=source_schema,
        source_table="secom_entities",
        target_schema="mart",
        target_table="secom_overview_test",
        connection_string=db_connection_string,
    )

    dialect = engine.dialect.name
    table_ref = (
        f"{source_schema}.secom_entities"
        if dialect != "sqlite"
        else "secom_entities"
    )
    staging_df = pd.read_sql(f"SELECT * FROM {table_ref}", engine)
    feature_cols = [c for c in staging_df.columns if c.startswith("feature_")]
    pass_count = int((staging_df["yield_label"] == -1).sum())
    fail_count = int((staging_df["yield_label"] == 1).sum())

    assert len(overview) == 1
    assert overview["entity_count"].iloc[0] == len(staging_df)
    assert overview["feature_count"].iloc[0] == len(feature_cols)
    assert overview["pass_count"].iloc[0] == pass_count
    assert overview["fail_count"].iloc[0] == fail_count
    assert np.isclose(
        overview["pass_pct"].iloc[0] + overview["fail_pct"].iloc[0], 1.0
    )


def test_feature_missingness_matches_catalog(engine, source_schema, db_connection_string):
    """mart.feature_missingness matches staging.feature_catalog."""
    missingness = build_feature_missingness(
        source_schema=source_schema,
        source_table="feature_catalog",
        target_schema="mart",
        target_table="feature_missingness_test",
        connection_string=db_connection_string,
    )

    dialect = engine.dialect.name
    table_ref = (
        f"{source_schema}.feature_catalog"
        if dialect != "sqlite"
        else "feature_catalog"
    )
    catalog_df = pd.read_sql(f"SELECT * FROM {table_ref}", engine)

    expected_columns = {
        "feature_name",
        "null_count",
        "null_pct",
        "distinct_count",
        "is_constant",
        "is_high_missing",
        "recommended_action",
    }
    assert set(missingness.columns) == expected_columns
    assert len(missingness) == len(catalog_df)
    # Ordered by null_pct DESC
    assert missingness["null_pct"].is_monotonic_decreasing


def test_label_distribution_percentages_sum_to_one(engine, source_schema, db_connection_string):
    """mart.label_distribution percentages sum to 1.0 within tolerance."""
    distribution = build_label_distribution(
        source_schema=source_schema,
        source_table="secom_entities",
        target_schema="mart",
        target_table="label_distribution_test",
        connection_string=db_connection_string,
    )

    assert distribution["entity_pct"].sum() == pytest.approx(1.0, abs=1e-9)


def test_top_signal_fail_separation_sorted_and_excludes_invalid(engine, source_schema, db_connection_string):
    """mart.top_signal_fail_separation is sorted by descending effect_size
    and excludes all-null/constant features."""
    result = build_top_signal_fail_separation(
        source_schema=source_schema,
        source_table="secom_entities",
        catalog_schema=source_schema,
        catalog_table="feature_catalog",
        target_schema="mart",
        target_table="top_signal_fail_separation_test",
        connection_string=db_connection_string,
    )

    dialect = engine.dialect.name
    catalog_ref = (
        f"{source_schema}.feature_catalog"
        if dialect != "sqlite"
        else "feature_catalog"
    )
    catalog_df = pd.read_sql(f"SELECT * FROM {catalog_ref}", engine)

    # Exclude NaN effect_sizes from sorting check
    valid_effect_sizes = result["effect_size"].dropna()
    if len(valid_effect_sizes) > 1:
        assert valid_effect_sizes.is_monotonic_decreasing

    # No features with zero pass or fail count
    assert (result["pass_count"] > 0).all()
    assert (result["fail_count"] > 0).all()

    # No constant or all-null features
    invalid_features = catalog_df[
        (catalog_df["is_constant"] == True) | (catalog_df["null_count"] == catalog_df["null_count"].max())
    ]["feature_name"].tolist()
    # More robust: get total_rows from secom_entities
    entities_ref = (
        f"{source_schema}.secom_entities"
        if dialect != "sqlite"
        else "secom_entities"
    )
    entities_df = pd.read_sql(f"SELECT * FROM {entities_ref}", engine)
    total_rows = len(entities_df)
    invalid_features = catalog_df[
        (catalog_df["is_constant"] == True) | (catalog_df["null_count"] == total_rows)
    ]["feature_name"].tolist()

    assert not result["feature_name"].isin(invalid_features).any()


def test_daily_yield_trend_reconciles_to_staging(engine, source_schema, db_connection_string):
    trend = build_daily_yield_trend(
        source_schema=source_schema,
        source_table="secom_entities",
        target_schema="mart",
        target_table="daily_yield_trend_test",
        connection_string=db_connection_string,
    )

    assert trend["entity_count"].sum() == 1567
    assert ((trend["pass_count"] + trend["fail_count"]) == trend["entity_count"]).all()
    assert ((trend["pass_rate"] + trend["fail_rate"]).round(10) == 1.0).all()


def test_feature_action_summary_reconciles_to_catalog(engine, source_schema, db_connection_string):
    summary = build_feature_action_summary(
        source_schema=source_schema,
        source_table="feature_catalog",
        target_schema="mart",
        target_table="feature_action_summary_test",
        connection_string=db_connection_string,
    )

    expected_actions = {
        "keep",
        "review_high_missing",
        "drop_constant",
        "drop_all_null",
    }

    assert summary["feature_count"].sum() == 590
    assert summary["feature_pct"].sum() == pytest.approx(1.0, abs=1e-9)
    assert set(summary["recommended_action"]).issubset(expected_actions)


def test_top_signal_profiles_row_count(engine, source_schema, db_connection_string):
    """mart.top_signal_profiles returns top_n * 2 rows with expected columns."""
    build_top_signal_fail_separation(
        source_schema=source_schema,
        source_table="secom_entities",
        catalog_schema=source_schema,
        catalog_table="feature_catalog",
        target_schema="mart",
        target_table="top_signal_fail_separation",
        connection_string=db_connection_string,
    )

    top_n = 20
    profiles = build_top_signal_profiles(
        top_n=top_n,
        source_schema=source_schema,
        source_table="secom_entities",
        ranking_schema="mart",
        ranking_table="top_signal_fail_separation",
        target_schema="mart",
        target_table="top_signal_profiles_test",
        connection_string=db_connection_string,
    )

    expected_columns = {
        "feature_name",
        "yield_class",
        "count",
        "missing_count",
        "mean",
        "stddev",
        "min",
        "p25",
        "median",
        "p75",
        "max",
    }

    assert set(profiles.columns) == expected_columns
    assert len(profiles) == top_n * 2
    assert (profiles["count"] >= 0).all()
    assert (profiles["missing_count"] >= 0).all()
    assert set(profiles["yield_class"]).issubset({"pass", "fail"})


def test_feature_failure_relationship_excludes_invalid(engine, source_schema, db_connection_string):
    """mart.feature_failure_relationship excludes constant/all-null features
    and includes effect_size and valid counts."""
    build_top_signal_fail_separation(
        source_schema=source_schema,
        source_table="secom_entities",
        catalog_schema=source_schema,
        catalog_table="feature_catalog",
        target_schema="mart",
        target_table="top_signal_fail_separation",
        connection_string=db_connection_string,
    )

    result = build_feature_failure_relationship(
        source_schema=source_schema,
        source_table="secom_entities",
        catalog_schema=source_schema,
        catalog_table="feature_catalog",
        target_schema="mart",
        target_table="feature_failure_relationship_test",
        connection_string=db_connection_string,
    )

    dialect = engine.dialect.name
    catalog_ref = (
        f"{source_schema}.feature_catalog"
        if dialect != "sqlite"
        else "feature_catalog"
    )
    catalog_df = pd.read_sql(f"SELECT * FROM {catalog_ref}", engine)
    entities_ref = (
        f"{source_schema}.secom_entities"
        if dialect != "sqlite"
        else "secom_entities"
    )
    entities_df = pd.read_sql(f"SELECT * FROM {entities_ref}", engine)
    total_rows = len(entities_df)

    invalid_features = catalog_df[
        (catalog_df["is_constant"] == True) | (catalog_df["null_count"] == total_rows)
    ]["feature_name"].tolist()

    assert not result["feature_name"].isin(invalid_features).any()
    assert "effect_size" in result.columns
    assert "valid_pass_count" in result.columns
    assert "valid_fail_count" in result.columns
    assert (result["valid_pass_count"] >= 0).all()
    assert (result["valid_fail_count"] >= 0).all()


def test_daily_failure_rollup_reconciles(engine, source_schema, db_connection_string):
    """mart.daily_failure_rollup reconciles to staging entity count."""
    rollup = build_daily_failure_rollup(
        source_schema=source_schema,
        source_table="secom_entities",
        target_schema="mart",
        target_table="daily_failure_rollup_test",
        connection_string=db_connection_string,
    )

    assert rollup["entity_count"].sum() == 1567
    assert (rollup["rolling_7d_fail_rate"] >= 0).all()
    assert (rollup["rolling_7d_fail_rate"] <= 1).all()


def test_feature_priority_index_buckets(engine, source_schema, db_connection_string):
    """mart.feature_priority_index assigns every feature exactly once
    and priority buckets follow the defined rules."""
    build_top_signal_fail_separation(
        source_schema=source_schema,
        source_table="secom_entities",
        catalog_schema=source_schema,
        catalog_table="feature_catalog",
        target_schema="mart",
        target_table="top_signal_fail_separation",
        connection_string=db_connection_string,
    )

    result = build_feature_priority_index(
        source_schema=source_schema,
        source_table="feature_catalog",
        ranking_schema="mart",
        ranking_table="top_signal_fail_separation",
        target_schema="mart",
        target_table="feature_priority_index_test",
        connection_string=db_connection_string,
    )

    assert result["feature_name"].is_unique
    assert len(result) == 590

    median_effect_size = result["effect_size"].dropna().median()

    for _, row in result.iterrows():
        expected_bucket = "standard_keep"
        if row["recommended_action"] == "drop_all_null":
            expected_bucket = "excluded_all_null"
        elif row["recommended_action"] == "drop_constant":
            expected_bucket = "excluded_constant"
        elif row["null_pct"] >= 0.50:
            expected_bucket = "review_high_missing"
        elif pd.notna(row["effect_size"]) and row["effect_size"] >= median_effect_size:
            expected_bucket = "top_separator"

        assert row["priority_bucket"] == expected_bucket, (
            f"Feature {row['feature_name']} expected {expected_bucket}, got {row['priority_bucket']}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
