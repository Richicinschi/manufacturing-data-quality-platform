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
    data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "secom"
    ingest_secom(
        data_path=data_dir / "secom.data",
        labels_path=data_dir / "secom_labels.data",
        schema="raw",
        connection_string=db_connection_string,
    )
    df = build_secom_entities(schema="raw", connection_string=db_connection_string)
    save_secom_entities(
        df,
        target_schema="staging",
        target_table="secom_entities",
        connection_string=db_connection_string,
    )
    build_feature_catalog(
        source_schema="staging",
        source_table="secom_entities",
        target_schema="staging",
        target_table="feature_catalog",
        connection_string=db_connection_string,
    )


def test_model_cv_results_mart(db_connection_string):
    df = build_model_cv_results(connection_string=db_connection_string)
    assert not df.empty
    assert {"model", "feature_set", "fold", "pr_auc"}.issubset(set(df.columns))


def test_model_benchmark_mart(db_connection_string):
    df = build_model_benchmark(connection_string=db_connection_string)
    assert not df.empty
    assert {"model", "feature_set", "mean_pr_auc", "rank"}.issubset(set(df.columns))
    # Ranks are dense and start at 1
    assert df["rank"].min() == 1


def test_model_threshold_analysis_mart(db_connection_string):
    df = build_model_threshold_analysis(connection_string=db_connection_string)
    assert not df.empty
    assert {"threshold", "precision", "recall", "f1", "selected"}.issubset(set(df.columns))
    assert df["selected"].sum() == 1


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
