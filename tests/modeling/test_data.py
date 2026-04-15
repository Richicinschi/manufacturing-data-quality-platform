"""Tests for src/modeling/data.py."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.etl.raw_ingest import ingest_secom
from src.etl.secom_join import build_secom_entities, save_secom_entities
from src.modeling.data import load_modeling_data


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
def load_data(db_connection_string):
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


def test_load_modeling_data_returns_expected_shapes(db_connection_string):
    X, y, timestamps = load_modeling_data(connection_string=db_connection_string)

    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert isinstance(timestamps, pd.Series)
    assert len(X) == len(y) == len(timestamps)
    assert len(X) == 1567
    # All feature columns start with feature_
    assert all(c.startswith("feature_") for c in X.columns)
    assert len(X.columns) == 590


def test_load_modeling_data_chronologically_sorted(db_connection_string):
    _, _, timestamps = load_modeling_data(connection_string=db_connection_string)
    assert timestamps.is_monotonic_increasing


def test_load_modeling_data_labels_encoded(db_connection_string):
    _, y, _ = load_modeling_data(connection_string=db_connection_string)
    assert set(y.unique()).issubset({0, 1})
    assert y.sum() == 104  # fail count
    assert (y == 0).sum() == 1463  # pass count


def test_load_modeling_data_no_global_imputation(db_connection_string):
    X, _, _ = load_modeling_data(connection_string=db_connection_string)
    assert X.isna().sum().sum() > 0, "Expected NaNs to be preserved (no global imputation)"
    assert not X.isna().all(axis=0).any(), "No column should be entirely null"
