"""Integration tests for modeling marts."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.etl.raw_ingest import ingest_secom
from src.etl.secom_join import build_secom_entities, save_secom_entities
from src.etl.feature_catalog import build_feature_catalog
from src.marts.model_cv_results import build_model_cv_results
from src.marts.model_benchmark import build_model_benchmark
from src.marts.model_threshold_analysis import build_model_threshold_analysis
from src.marts.final_model_test_results import build_final_model_test_results
from src.marts.model_confusion_summary import build_model_confusion_summary
from src.marts.selected_signal_shortlist import build_selected_signal_shortlist
from src.marts.model_registry import build_model_registry
from src.marts.model_feature_importance import build_model_feature_importance
from src.marts.model_threshold_cost_curve import build_model_threshold_cost_curve
from src.marts.model_probability_bins import build_model_probability_bins
from src.marts.model_inspection_metrics import build_model_inspection_metrics
from src.marts.model_feature_selection_summary import build_model_feature_selection_summary
from src.marts.anomaly_model_benchmark import build_anomaly_model_benchmark
from src.marts.final_model_inspection_curve import build_final_model_inspection_curve
from src.marts.public_notebook_comparison import build_public_notebook_comparison
from src.modeling.evaluator import find_best_model
from src.modeling import trainer as trainer_module
from src.modeling import pipeline_runner as pipeline_runner_module


@pytest.fixture(autouse=True)
def fast_walk_forward(monkeypatch):
    """Reduce CV folds and min_fails in integration tests to keep runtime reasonable."""
    original = trainer_module.run_walk_forward_cv
    def _fast_run(X, y, timestamps, feature_sets, n_splits=4, min_fails=8):
        return original(X, y, timestamps, feature_sets, n_splits=2, min_fails=3)
    monkeypatch.setattr(pipeline_runner_module, "run_walk_forward_cv", _fast_run)


@pytest.fixture(autouse=True)
def temp_artifact_dir(monkeypatch):
    """Redirect model artifact output to a temporary directory during tests."""
    artifact_tmp = tempfile.mkdtemp(prefix="test_artifacts_")
    monkeypatch.setenv("SECOM_ARTIFACT_DIR", artifact_tmp)
    pipeline_runner_module._run_pipeline_cached.cache_clear()
    yield
    pipeline_runner_module._run_pipeline_cached.cache_clear()
    try:
        import shutil
        shutil.rmtree(artifact_tmp)
    except Exception:
        pass


@pytest.fixture(scope="module")
def db_connection_string():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    yield f"sqlite:///{tmp_path}"
    try:
        os.unlink(tmp_path)
    except PermissionError:
        pass


@pytest.fixture(scope="module", autouse=True)
def load_staging_data(db_connection_string):
    """Load small synthetic data directly into staging to keep tests fast."""
    import numpy as np
    from sqlalchemy import create_engine

    rng = np.random.default_rng(42)
    n_rows = 120
    n_features = 12

    timestamps = pd.date_range("2023-01-01", periods=n_rows, freq="h")
    # Ensure enough fails for CV
    yield_label = np.array([1] * 20 + [-1] * 100)
    rng.shuffle(yield_label)
    pass_fail = np.where(yield_label == 1, "fail", "pass")

    df = pd.DataFrame({
        "entity_id": range(n_rows),
        "test_timestamp": timestamps,
        "yield_label": yield_label,
        "pass_fail": pass_fail,
    })
    for i in range(n_features):
        df[f"feature_{i+1:03d}"] = rng.standard_normal(n_rows)
        # Make first feature somewhat predictive
        if i == 0:
            df.loc[yield_label == 1, f"feature_{i+1:03d}"] += 1.5
        # Make one feature mostly missing (review_high_missing)
        if i == 1:
            df.loc[rng.choice(n_rows, size=n_rows // 2, replace=False), f"feature_{i+1:03d}"] = np.nan
        # Make one feature constant
        if i == 2:
            df[f"feature_{i+1:03d}"] = 5.0

    engine = create_engine(db_connection_string)
    try:
        df.to_sql("secom_entities", con=engine, if_exists="replace", index=False)

        build_feature_catalog(
            source_schema="staging",
            source_table="secom_entities",
            target_schema="staging",
            target_table="feature_catalog",
            connection_string=db_connection_string,
        )
    finally:
        engine.dispose()


def test_model_cv_results_mart(db_connection_string):
    df = build_model_cv_results(connection_string=db_connection_string)
    assert not df.empty
    assert {"model", "feature_set", "fold", "pr_auc"}.issubset(set(df.columns))
    # New columns should be present
    assert "n_features_requested" in df.columns
    assert "n_features_used" in df.columns
    assert "train_start_date" in df.columns
    assert "test_fails" in df.columns


def test_model_benchmark_mart(db_connection_string):
    df = build_model_benchmark(connection_string=db_connection_string)
    assert not df.empty
    assert {"model", "feature_set", "mean_pr_auc", "rank"}.issubset(set(df.columns))
    assert "model_family" in df.columns
    assert "final_eligible" in df.columns
    assert "enabled" in df.columns
    assert "mean_precision" in df.columns
    assert "mean_recall" in df.columns
    assert "mean_balanced_accuracy" in df.columns
    # Ranks are dense and start at 1
    assert df["rank"].min() == 1


def test_model_threshold_analysis_mart(db_connection_string):
    df = build_model_threshold_analysis(connection_string=db_connection_string)
    assert not df.empty
    assert {"threshold", "precision", "recall", "f1", "selected"}.issubset(set(df.columns))
    assert df["selected"].sum() == 1


def test_model_threshold_cost_curve_mart(db_connection_string):
    df = build_model_threshold_cost_curve(connection_string=db_connection_string)
    assert not df.empty
    assert {
        "threshold", "precision", "recall", "f1",
        "predicted_fail_count", "false_positive_count", "false_negative_count", "inspection_rate", "selected"
    }.issubset(set(df.columns))
    assert df["selected"].sum() == 1


def test_model_probability_bins_mart(db_connection_string):
    df = build_model_probability_bins(connection_string=db_connection_string)
    assert not df.empty
    assert {"bin_min", "bin_max", "total_entities", "fail_count", "fail_rate"}.issubset(set(df.columns))


def test_model_feature_importance_mart(db_connection_string):
    df = build_model_feature_importance(connection_string=db_connection_string)
    assert not df.empty
    assert {"feature_name", "importance", "importance_type"}.issubset(set(df.columns))


def test_model_registry_mart(db_connection_string):
    df = build_model_registry(connection_string=db_connection_string)
    assert not df.empty
    assert {"model_id", "model_family", "final_eligible", "enabled", "skip_reason"}.issubset(set(df.columns))


def test_final_model_test_results_mart(db_connection_string):
    df = build_final_model_test_results(connection_string=db_connection_string)
    assert len(df) == 1
    assert {"model", "feature_set", "test_pr_auc"}.issubset(set(df.columns))


def test_model_confusion_summary_mart(db_connection_string):
    df = build_model_confusion_summary(connection_string=db_connection_string)
    assert not df.empty
    assert {"split", "tn", "fp", "fn", "tp"}.issubset(set(df.columns))
    test_row = df[df["split"] == "test"]
    assert len(test_row) == 1


def test_selected_signal_shortlist_mart(db_connection_string):
    df = build_selected_signal_shortlist(connection_string=db_connection_string)
    assert not df.empty
    assert {"feature_name", "effect_rank", "recommended_action"}.issubset(set(df.columns))
    # All effect ranks are reasonable integers
    assert (df["effect_rank"] > 0).all()


def test_model_inspection_metrics_mart(db_connection_string):
    df = build_model_inspection_metrics(connection_string=db_connection_string)
    assert not df.empty
    assert "mean_recall_at_10pct" in df.columns
    assert "mean_precision_at_10pct" in df.columns
    assert "mean_lift_at_10pct" in df.columns


def test_model_feature_selection_summary_mart(db_connection_string):
    df = build_model_feature_selection_summary(connection_string=db_connection_string)
    assert not df.empty
    assert {"model", "feature_set", "mean_n_selected"}.issubset(set(df.columns))


def test_anomaly_model_benchmark_mart(db_connection_string):
    df = build_anomaly_model_benchmark(connection_string=db_connection_string)
    assert not df.empty
    assert (df["model_kind"] == "anomaly_detector").all()


def test_final_model_inspection_curve_mart(db_connection_string):
    df = build_final_model_inspection_curve(connection_string=db_connection_string)
    assert not df.empty
    assert {"inspection_rate", "recall", "precision", "lift"}.issubset(set(df.columns))


def test_public_notebook_comparison_mart(db_connection_string):
    df = build_public_notebook_comparison(connection_string=db_connection_string)
    # Should be empty if comparison script has not been run
    assert len(df) == 0 or "evaluation_protocol" in df.columns


def test_final_model_selection_ignores_non_eligible_models():
    cv_results = pd.DataFrame(
        {
            "model": ["dummy_stratified", "random_forest", "random_forest"],
            "feature_set": ["keep_only", "keep_only", "keep_only"],
            "fold": [1, 1, 2],
            "pr_auc": [0.90, 0.20, 0.25],
            "final_eligible": [False, True, True],
            "enabled": [True, True, True],
        }
    )
    best = find_best_model(cv_results)
    assert best["model"] == "random_forest"
    assert best["feature_set"] == "keep_only"
