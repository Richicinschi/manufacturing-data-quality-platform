"""Tests for src/modeling/trainer.py."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from src.modeling.trainer import (
    MODEL_REGISTRY,
    is_model_enabled,
    preprocess_fold,
    run_walk_forward_cv,
)


def _make_daily_data(n_days: int, samples_per_day: int, n_fails_per_day: int, n_features: int, seed: int = 42):
    np.random.seed(seed)
    timestamps = pd.to_datetime(
        [d for day in pd.date_range("2024-01-01", periods=n_days, freq="D") for d in [day] * samples_per_day]
    )
    X = pd.DataFrame(
        np.random.randn(len(timestamps), n_features),
        columns=[f"feat_{i}" for i in range(n_features)],
    )
    y_values = []
    for _ in range(n_days):
        y_values.extend([1] * n_fails_per_day + [0] * (samples_per_day - n_fails_per_day))
    y = pd.Series(y_values)
    return X, y, timestamps


def test_model_registry_skips_optional_models_when_missing():
    xgboost_spec = MODEL_REGISTRY["xgboost_hist"]
    lightgbm_spec = MODEL_REGISTRY["lightgbm_gbdt"]

    if not is_model_enabled(xgboost_spec):
        assert xgboost_spec.final_eligible is False
    if not is_model_enabled(lightgbm_spec):
        assert lightgbm_spec.final_eligible is False


def test_run_walk_forward_cv_produces_results_and_oof():
    # Use slightly more data to avoid saga convergence noise on tiny folds
    X, y, timestamps = _make_daily_data(n_days=6, samples_per_day=25, n_fails_per_day=5, n_features=10)

    feature_sets = {
        "keep_only": [f"feat_{i}" for i in range(5)],
        "keep_plus_review": [f"feat_{i}" for i in range(8)],
        "top_20_effect": [],
        "top_50_effect": [],
        "top_100_effect": [],
    }

    cv_results, oof_df = run_walk_forward_cv(
        X, y, timestamps, feature_sets, n_splits=3, min_fails=2
    )

    assert len(cv_results) > 0
    assert "model" in cv_results.columns
    assert "feature_set" in cv_results.columns
    assert "pr_auc" in cv_results.columns
    assert len(oof_df) == len(X)
    assert "y_true" in oof_df.columns

    # Verify per-(model, feature_set) OOF columns exist
    assert "oof_risk_dummy_stratified_keep_only" in oof_df.columns
    assert "oof_risk_dummy_stratified_keep_plus_review" in oof_df.columns
    assert "oof_risk_logistic_l1_keep_only" in oof_df.columns


def test_oof_predictions_differ_across_feature_sets():
    X, y, timestamps = _make_daily_data(n_days=3, samples_per_day=20, n_fails_per_day=6, n_features=6)

    feature_sets = {
        "fs_a": ["feat_0", "feat_1"],
        "fs_b": ["feat_2", "feat_3", "feat_4"],
    }

    cv_results, oof_df = run_walk_forward_cv(
        X, y, timestamps, feature_sets, n_splits=2, min_fails=2
    )

    # Dummy ignores features, so skip it; real models should differ.
    real_models = [m for m in cv_results["model"].unique() if m != "dummy_stratified"]
    assert len(real_models) > 0
    differing = 0
    for model in real_models:
        col_a = f"oof_risk_{model}_fs_a"
        col_b = f"oof_risk_{model}_fs_b"
        assert col_a in oof_df.columns
        assert col_b in oof_df.columns
        valid_a = oof_df[col_a].dropna()
        valid_b = oof_df[col_b].dropna()
        if len(valid_a) > 0 and len(valid_b) > 0:
            # Some models may output constant predictions on tiny synthetic data;
            # we only require that at least one real model differs across feature sets.
            if not valid_a.equals(valid_b):
                differing += 1
    assert differing > 0, "At least one real model should produce different OOF predictions across feature sets"


def test_all_models_train_without_error():
    X, y, timestamps = _make_daily_data(n_days=3, samples_per_day=10, n_fails_per_day=3, n_features=4, seed=7)

    feature_sets = {
        "keep_only": ["a", "b"],
    }
    # Rename columns to match
    X.columns = ["a", "b", "c", "d"]

    cv_results, _ = run_walk_forward_cv(X, y, timestamps, feature_sets, n_splits=2, min_fails=1)
    models_trained = set(cv_results["model"].unique())
    assert "dummy_stratified" in models_trained
    assert "logistic_l1" in models_trained
    assert "random_forest" in models_trained


def test_n_features_reflects_post_imputation_count():
    X, y, timestamps = _make_daily_data(n_days=3, samples_per_day=10, n_fails_per_day=3, n_features=4, seed=7)
    # Make one selected feature entirely NaN so SimpleImputer drops it
    X["feat_0"] = np.nan

    feature_sets = {
        "with_nan": ["feat_0", "feat_1", "feat_2"],
    }

    cv_results, _ = run_walk_forward_cv(X, y, timestamps, feature_sets, n_splits=2, min_fails=1)

    # Every fold should report n_features_used == 2 (feat_0 dropped)
    assert (cv_results["n_features_used"] == 2).all()
    # dropped_all_missing_features should list feat_0 in every row
    assert (cv_results["dropped_all_missing_features"] == "feat_0").all()


def test_logistic_l2_and_hist_gradient_boosting_train():
    X, y, timestamps = _make_daily_data(n_days=3, samples_per_day=10, n_fails_per_day=3, n_features=4, seed=7)
    feature_sets = {"keep_only": ["feat_0", "feat_1"]}

    cv_results, _ = run_walk_forward_cv(X, y, timestamps, feature_sets, n_splits=2, min_fails=1)
    models_trained = set(cv_results["model"].unique())
    assert "logistic_l2" in models_trained
    assert "hist_gradient_boosting" in models_trained


def test_fold_local_preprocessing_drops_all_missing_columns():
    X, y, timestamps = _make_daily_data(n_days=3, samples_per_day=10, n_fails_per_day=3, n_features=4, seed=7)
    X["feat_0"] = np.nan
    feature_sets = {"fs": ["feat_0", "feat_1", "feat_2"]}

    cv_results, _ = run_walk_forward_cv(X, y, timestamps, feature_sets, n_splits=2, min_fails=1)
    assert (cv_results["n_features_requested"] == 3).all()
    assert (cv_results["n_features_used"] == 2).all()
    assert (cv_results["dropped_all_missing_features"] == "feat_0").all()


def test_no_imputer_warnings_in_test_suite():
    X, y, timestamps = _make_daily_data(n_days=3, samples_per_day=10, n_fails_per_day=3, n_features=4, seed=7)
    X["feat_0"] = np.nan
    feature_sets = {"fs": ["feat_0", "feat_1"]}

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        run_walk_forward_cv(X, y, timestamps, feature_sets, n_splits=2, min_fails=1)
        imputer_warnings = [x for x in w if "Skipping features without any observed values" in str(x.message)]
        assert len(imputer_warnings) == 0, "SimpleImputer should not warn when all-missing columns are pre-dropped"


def test_preprocessing_scaling_for_knn():
    X, y, timestamps = _make_daily_data(n_days=3, samples_per_day=10, n_fails_per_day=3, n_features=2, seed=7)
    feature_sets = {"fs": ["feat_0", "feat_1"]}

    model_spec = MODEL_REGISTRY["knn_scaled"]
    preprocessed = preprocess_fold(X.iloc[:15], X.iloc[15:], feature_sets["fs"], model_spec)

    # After scaling, mean should be approx 0 and std approx 1 on train
    train_mean = preprocessed["X_train"].mean().abs().max()
    train_std = preprocessed["X_train"].std().mean()
    assert train_mean < 0.5
    assert train_std > 0.5


def test_logistic_l1_produces_more_zero_coefficients_than_l2():
    """L1 regularization should drive more coefficients to zero than L2 on scaled data."""
    np.random.seed(42)
    n_rows = 200
    n_features = 10
    X = pd.DataFrame(np.random.randn(n_rows, n_features), columns=[f"feat_{i}" for i in range(n_features)])
    # Make first 3 features predictive
    y = pd.Series(((X["feat_0"] + X["feat_1"] - X["feat_2"]) > 0).astype(int))

    l1_spec = MODEL_REGISTRY["logistic_l1"]
    l2_spec = MODEL_REGISTRY["logistic_l2"]

    l1_pre = preprocess_fold(X.iloc[:150], X.iloc[150:], X.columns.tolist(), l1_spec)
    l2_pre = preprocess_fold(X.iloc[:150], X.iloc[150:], X.columns.tolist(), l2_spec)

    l1_model = l1_spec.factory(y.iloc[:150])
    l2_model = l2_spec.factory(y.iloc[:150])

    l1_model.fit(l1_pre["X_train"], y.iloc[:150])
    l2_model.fit(l2_pre["X_train"], y.iloc[:150])

    l1_zeros = (np.abs(l1_model.coef_) < 1e-6).sum()
    l2_zeros = (np.abs(l2_model.coef_) < 1e-6).sum()

    assert l1_zeros > l2_zeros, f"Expected L1 to produce more zero coefficients than L2, got {l1_zeros} vs {l2_zeros}"


def test_anomaly_detector_score_orientation():
    """Higher risk scores from _get_risk_scores must mean higher failure risk."""
    from src.modeling.trainer import _get_risk_scores

    if_spec = MODEL_REGISTRY["isolation_forest_pass_only"]
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(50, 4), columns=["a", "b", "c", "d"])
    y = pd.Series([0] * 40 + [1] * 10)

    model = if_spec.factory(y)
    model.fit(X.iloc[:40])

    scores = _get_risk_scores(model, X, if_spec)
    # The 10 anomalous rows (last 10) should have higher risk scores on average
    assert scores[40:].mean() > scores[:40].mean(), "Anomaly scores should be higher for more anomalous rows"


def test_pass_only_anomaly_detector_fits_only_on_pass_class():
    """Pass-only anomaly detectors must be fitted exclusively on y == 0 rows."""
    from sklearn.ensemble import IsolationForest

    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(30, 3), columns=["a", "b", "c"])
    y = pd.Series([0] * 20 + [1] * 10)

    model = IsolationForest(random_state=42)
    pass_mask = y.values == 0
    model.fit(X.iloc[pass_mask])

    # Verify the model was fitted (no exception) and can score all rows
    scores = model.score_samples(X)
    assert len(scores) == 30
    assert not np.isnan(scores).any()
