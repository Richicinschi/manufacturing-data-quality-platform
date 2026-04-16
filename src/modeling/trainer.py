"""Model trainer with walk-forward CV and per-fold feature selection."""

from __future__ import annotations

import importlib
import json
import warnings
from dataclasses import dataclass, field
from time import perf_counter
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.covariance import EllipticEnvelope
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.neighbors import KNeighborsClassifier, LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from src.modeling.cv_engine import expanding_window_splits
from src.modeling.features import (
    build_missingness_indicator_features,
    compute_correlation_pruned_features,
    compute_top_n_auc_gap_features,
    compute_top_n_effect_features,
    compute_top_n_mutual_info_features,
)
from src.modeling.inspection import compute_inspection_metrics


@dataclass
class ModelSpec:
    model_id: str
    family: str
    requires_imputation: bool
    requires_scaling: bool
    handles_nan: bool
    final_eligible: bool
    optional_dependency: str | None
    factory: Callable[[pd.Series], object]
    model_kind: str = "classifier"
    fit_mode: str = "all_train"
    score_method: str = "predict_proba"
    higher_score_is_failure_risk: bool = True
    enabled_by_default: bool = True


def _log_progress(message: str) -> None:
    print(message, flush=True)


def _is_installed(package_name: str) -> bool:
    try:
        importlib.import_module(package_name)
        return True
    except Exception:
        return False


def _scale_pos_weight(y_train: pd.Series) -> float:
    n_pos = int(y_train.sum())
    n_neg = len(y_train) - n_pos
    if n_pos == 0:
        return 1.0
    return n_neg / n_pos


def _build_model_registry() -> dict[str, ModelSpec]:
    registry: dict[str, ModelSpec] = {}

    registry["dummy_stratified"] = ModelSpec(
        model_id="dummy_stratified",
        family="baseline",
        requires_imputation=False,
        requires_scaling=False,
        handles_nan=False,
        final_eligible=False,
        optional_dependency=None,
        factory=lambda y_train: DummyClassifier(strategy="stratified", random_state=42),
    )

    registry["logistic_l1"] = ModelSpec(
        model_id="logistic_l1",
        family="linear",
        requires_imputation=True,
        requires_scaling=True,
        handles_nan=False,
        final_eligible=True,
        optional_dependency=None,
        factory=lambda y_train: LogisticRegression(
            class_weight="balanced",
            solver="saga",
            l1_ratio=1.0,
            max_iter=5000,
            C=1.0,
            random_state=42,
        ),
    )

    registry["logistic_l2"] = ModelSpec(
        model_id="logistic_l2",
        family="linear",
        requires_imputation=True,
        requires_scaling=True,
        handles_nan=False,
        final_eligible=True,
        optional_dependency=None,
        factory=lambda y_train: LogisticRegression(
            class_weight="balanced",
            solver="lbfgs",
            l1_ratio=0.0,
            max_iter=2000,
            C=1.0,
            random_state=42,
        ),
    )

    registry["random_forest"] = ModelSpec(
        model_id="random_forest",
        family="bagged_trees",
        requires_imputation=True,
        requires_scaling=False,
        handles_nan=False,
        final_eligible=True,
        optional_dependency=None,
        factory=lambda y_train: RandomForestClassifier(
            class_weight="balanced",
            n_estimators=200,
            max_depth=8,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
    )

    registry["hist_gradient_boosting"] = ModelSpec(
        model_id="hist_gradient_boosting",
        family="boosted_trees",
        requires_imputation=False,
        requires_scaling=False,
        handles_nan=True,
        final_eligible=True,
        optional_dependency=None,
        factory=lambda y_train: HistGradientBoostingClassifier(
            max_depth=6,
            max_iter=200,
            early_stopping=False,
            random_state=42,
        ),
    )

    xgboost_installed = _is_installed("xgboost")
    registry["xgboost_hist"] = ModelSpec(
        model_id="xgboost_hist",
        family="boosted_trees",
        requires_imputation=False,
        requires_scaling=False,
        handles_nan=True,
        final_eligible=xgboost_installed,
        optional_dependency="xgboost",
        factory=lambda y_train: _build_xgboost(_scale_pos_weight(y_train)),
    )

    lightgbm_installed = _is_installed("lightgbm")
    registry["lightgbm_gbdt"] = ModelSpec(
        model_id="lightgbm_gbdt",
        family="boosted_trees",
        requires_imputation=False,
        requires_scaling=False,
        handles_nan=True,
        final_eligible=lightgbm_installed,
        optional_dependency="lightgbm",
        factory=lambda y_train: _build_lightgbm(_scale_pos_weight(y_train)),
    )

    registry["knn_scaled"] = ModelSpec(
        model_id="knn_scaled",
        family="distance_based",
        requires_imputation=True,
        requires_scaling=True,
        handles_nan=False,
        final_eligible=False,
        optional_dependency=None,
        factory=lambda y_train: KNeighborsClassifier(n_neighbors=5),
    )

    # Anomaly detection models
    registry["isolation_forest_pass_only"] = ModelSpec(
        model_id="isolation_forest_pass_only",
        family="anomaly_detection",
        requires_imputation=True,
        requires_scaling=True,
        handles_nan=False,
        final_eligible=True,
        optional_dependency=None,
        factory=lambda y_train: IsolationForest(
            n_estimators=200,
            contamination="auto",
            random_state=42,
            n_jobs=-1,
        ),
        model_kind="anomaly_detector",
        fit_mode="pass_only",
        score_method="score_samples",
        higher_score_is_failure_risk=False,
    )

    registry["local_outlier_factor_pass_only"] = ModelSpec(
        model_id="local_outlier_factor_pass_only",
        family="anomaly_detection",
        requires_imputation=True,
        requires_scaling=True,
        handles_nan=False,
        final_eligible=True,
        optional_dependency=None,
        factory=lambda y_train: LocalOutlierFactor(
            n_neighbors=min(20, max(5, int((y_train == 0).sum() * 0.5))) if (y_train == 0).sum() > 0 else 5,
            novelty=True,
            n_jobs=-1,
        ),
        model_kind="anomaly_detector",
        fit_mode="pass_only",
        score_method="score_samples",
        higher_score_is_failure_risk=False,
    )

    registry["elliptic_envelope_pass_only"] = ModelSpec(
        model_id="elliptic_envelope_pass_only",
        family="anomaly_detection",
        requires_imputation=True,
        requires_scaling=True,
        handles_nan=False,
        final_eligible=True,
        optional_dependency=None,
        factory=lambda y_train: EllipticEnvelope(
            contamination=0.1,
            random_state=42,
        ),
        model_kind="anomaly_detector",
        fit_mode="pass_only",
        score_method="score_samples",
        higher_score_is_failure_risk=False,
        enabled_by_default=False,
    )

    registry["one_class_svm_pass_only"] = ModelSpec(
        model_id="one_class_svm_pass_only",
        family="anomaly_detection",
        requires_imputation=True,
        requires_scaling=True,
        handles_nan=False,
        final_eligible=False,
        optional_dependency=None,
        factory=lambda y_train: OneClassSVM(),
        model_kind="anomaly_detector",
        fit_mode="pass_only",
        score_method="decision_function",
        higher_score_is_failure_risk=False,
        enabled_by_default=False,
    )

    registry["isolation_forest_all_train"] = ModelSpec(
        model_id="isolation_forest_all_train",
        family="anomaly_detection",
        requires_imputation=True,
        requires_scaling=True,
        handles_nan=False,
        final_eligible=False,
        optional_dependency=None,
        factory=lambda y_train: IsolationForest(
            n_estimators=200,
            contamination="auto",
            random_state=42,
            n_jobs=-1,
        ),
        model_kind="anomaly_detector",
        enabled_by_default=False,
        fit_mode="all_train",
        score_method="score_samples",
        higher_score_is_failure_risk=False,
    )

    return registry


def _build_xgboost(scale_pos_weight: float):
    from xgboost import XGBClassifier

    return XGBClassifier(
        tree_method="hist",
        use_label_encoder=False,
        eval_metric="logloss",
        scale_pos_weight=scale_pos_weight,
        max_depth=6,
        n_estimators=200,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1,
    )


def _build_lightgbm(scale_pos_weight: float):
    from lightgbm import LGBMClassifier

    return LGBMClassifier(
        objective="binary",
        scale_pos_weight=scale_pos_weight,
        max_depth=6,
        n_estimators=200,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )


MODEL_REGISTRY = _build_model_registry()


def is_model_enabled(model_spec: ModelSpec) -> bool:
    if not model_spec.enabled_by_default:
        return False
    if model_spec.optional_dependency is None:
        return True
    return _is_installed(model_spec.optional_dependency)


def preprocess_fold(
    X_train_full: pd.DataFrame,
    X_test_full: pd.DataFrame,
    selected_features: list[str],
    model_spec: ModelSpec,
) -> dict:
    """Prepare fold-local train/test matrices with honest feature counts.

    Returns dict with:
        X_train, X_test, n_features_requested, n_features_used,
        dropped_all_missing_features, imputer, scaler
    """
    n_features_requested = len(selected_features)
    imputer = None
    scaler = None

    # Drop columns that are entirely missing in the training fold
    train_subset = X_train_full[selected_features]
    all_missing = train_subset.columns[train_subset.isna().all()].tolist()
    remaining_features = [c for c in selected_features if c not in all_missing]
    dropped_all_missing_features = ", ".join(sorted(all_missing))

    if len(remaining_features) == 0:
        raise ValueError("All selected features are missing in the training fold.")

    X_train = X_train_full[remaining_features].copy()
    X_test = X_test_full[remaining_features].copy()

    if model_spec.requires_imputation:
        with warnings.catch_warnings():
            # SimpleImputer(median) on all-NaN columns triggers numpy RuntimeWarnings.
            warnings.filterwarnings("ignore", message="All-NaN slice encountered", category=RuntimeWarning)
            warnings.filterwarnings("ignore", message="Mean of empty slice", category=RuntimeWarning)
            imputer = SimpleImputer(strategy="median")
            X_train_arr = imputer.fit_transform(X_train)
            X_test_arr = imputer.transform(X_test)
        imputed_features = imputer.get_feature_names_out().tolist()
        X_train = pd.DataFrame(X_train_arr, columns=imputed_features, index=X_train.index)
        X_test = pd.DataFrame(X_test_arr, columns=imputed_features, index=X_test.index)

    if model_spec.requires_scaling:
        scaler = StandardScaler()
        X_train_arr = scaler.fit_transform(X_train)
        X_test_arr = scaler.transform(X_test)
        X_train = pd.DataFrame(X_train_arr, columns=X_train.columns, index=X_train.index)
        X_test = pd.DataFrame(X_test_arr, columns=X_test.columns, index=X_test.index)

    return {
        "X_train": X_train,
        "X_test": X_test,
        "n_features_requested": n_features_requested,
        "n_features_used": len(remaining_features),
        "dropped_all_missing_features": dropped_all_missing_features,
        "imputer": imputer,
        "scaler": scaler,
    }


def _resolve_feature_set(
    fs_name: str,
    X_train_full: pd.DataFrame,
    y_train: pd.Series,
    base_features: list[str],
    static_feature_sets: dict[str, list[str]],
) -> tuple[list[str], pd.DataFrame, pd.DataFrame]:
    """Resolve dynamic feature sets inside a training fold.

    Returns (selected_features, transformed_X_train, transformed_X_test).
    For most feature sets, transformed_X_train == X_train_full and same for test.
    For missingness_indicators_keep, the DataFrames are expanded with indicator columns.
    """
    if fs_name == "top_20_effect":
        return compute_top_n_effect_features(X_train_full, y_train, 20), X_train_full, None
    elif fs_name == "top_50_effect":
        return compute_top_n_effect_features(X_train_full, y_train, 50), X_train_full, None
    elif fs_name == "top_100_effect":
        return compute_top_n_effect_features(X_train_full, y_train, 100), X_train_full, None
    elif fs_name == "correlation_pruned_070":
        base = static_feature_sets.get("keep_plus_review", X_train_full.columns.tolist())
        features = compute_correlation_pruned_features(X_train_full[base], threshold=0.70)
        return features, X_train_full, None
    elif fs_name == "correlation_pruned_085":
        base = static_feature_sets.get("keep_plus_review", X_train_full.columns.tolist())
        features = compute_correlation_pruned_features(X_train_full[base], threshold=0.85)
        return features, X_train_full, None
    elif fs_name == "top_25_mutual_info":
        return compute_top_n_mutual_info_features(X_train_full, y_train, 25), X_train_full, None
    elif fs_name == "top_50_mutual_info":
        return compute_top_n_mutual_info_features(X_train_full, y_train, 50), X_train_full, None
    elif fs_name == "top_25_auc_gap":
        return compute_top_n_auc_gap_features(X_train_full, y_train, 25), X_train_full, None
    elif fs_name == "top_50_auc_gap":
        return compute_top_n_auc_gap_features(X_train_full, y_train, 50), X_train_full, None
    elif fs_name == "missingness_indicators_keep":
        base = static_feature_sets.get("keep_only", X_train_full.columns.tolist())
        X_train_mi, mi_features = build_missingness_indicator_features(X_train_full, base)
        return mi_features, X_train_mi, None
    else:
        return base_features, X_train_full, None


def _get_risk_scores(model, X_test: pd.DataFrame, model_spec: ModelSpec) -> np.ndarray:
    """Extract unified risk scores from a fitted model.

    Higher score always means higher failure risk.
    """
    if model_spec.score_method == "predict_proba":
        return model.predict_proba(X_test)[:, 1]

    score_fn = getattr(model, model_spec.score_method)
    # sklearn >=1.8 LocalOutlierFactor emits a spurious feature-names warning
    # during score_samples even when X is a DataFrame with valid names.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="X does not have valid feature names, but .* was fitted with feature names",
            category=UserWarning,
        )
        scores = score_fn(X_test)

    if not model_spec.higher_score_is_failure_risk:
        scores = -scores

    return np.asarray(scores)


def run_walk_forward_cv(
    X: pd.DataFrame,
    y: pd.Series,
    timestamps: pd.Series,
    feature_sets: dict[str, list[str]],
    n_splits: int = 4,
    min_fails: int = 8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run walk-forward CV for all models and feature sets.

    Args:
        X: Feature DataFrame with NaNs preserved.
        y: Binary labels.
        timestamps: Timestamps.
        feature_sets: Dict of feature set name -> list of feature names.
                      Must include 'keep_only' and 'keep_plus_review'.
        n_splits: Target CV splits.
        min_fails: Minimum fails per fold.

    Returns:
        (cv_results_df, oof_predictions_df)
            cv_results_df: one row per (model, feature_set, fold)
            oof_predictions_df: one row per sample with OOF risk score columns
    """
    splits = expanding_window_splits(X, y, timestamps, n_splits=n_splits, min_fails=min_fails)
    actual_n_splits = len(splits)

    static_feature_sets = {
        k: v for k, v in feature_sets.items()
        if k in ("keep_only", "keep_plus_review")
    }

    oof_keys = [(name, fs) for name in MODEL_REGISTRY for fs in feature_sets]
    oof_scores = {key: np.full(len(X), np.nan) for key in oof_keys}

    records = []
    runtime_records = []

    enabled_models = [(name, spec) for name, spec in MODEL_REGISTRY.items() if is_model_enabled(spec)]
    total_configs = len(enabled_models) * len(feature_sets)
    config_idx = 0
    pipeline_start = perf_counter()

    for model_name, model_spec in enabled_models:
        enabled = True
        for fs_name, fs_features in feature_sets.items():
            config_idx += 1
            config_start = perf_counter()
            _log_progress(
                f"[cv] START {config_idx:03d}/{total_configs} model={model_name} "
                f"feature_set={fs_name} kind={model_spec.model_kind} final_eligible={model_spec.final_eligible}"
            )
            for fold_idx, (train_idx, test_idx) in enumerate(splits, start=1):
                X_train_full = X.iloc[train_idx]
                y_train = y.iloc[train_idx]
                X_test_full = X.iloc[test_idx]
                y_test = y.iloc[test_idx]

                # Resolve dynamic feature sets inside the fold
                selected_features, X_train_resolved, _ = _resolve_feature_set(
                    fs_name, X_train_full, y_train, fs_features, static_feature_sets
                )

                # For missingness_indicators_keep, expand test with same indicators
                if fs_name == "missingness_indicators_keep":
                    base = static_feature_sets.get("keep_only", X_train_full.columns.tolist())
                    X_test_resolved = X_test_full[base].copy()
                    indicators = {
                        f"{col}_missing": X_test_resolved[col].isna().astype(int)
                        for col in base
                        if f"{col}_missing" in selected_features
                    }
                    if indicators:
                        X_test_resolved = pd.concat(
                            [X_test_resolved, pd.DataFrame(indicators, index=X_test_resolved.index)], axis=1
                        )
                else:
                    X_test_resolved = X_test_full

                _log_progress(
                    f"[cv]   fold={fold_idx}/{actual_n_splits} "
                    f"train_rows={len(train_idx)} test_rows={len(test_idx)} "
                    f"train_fails={int(y_train.sum())} test_fails={int(y_test.sum())}"
                )

                if len(selected_features) == 0:
                    _log_progress(f"[cv]   fold={fold_idx} skipped: empty feature set")
                    continue

                try:
                    preprocessed = preprocess_fold(
                        X_train_resolved, X_test_resolved, selected_features, model_spec
                    )
                except ValueError as exc:
                    _log_progress(f"[cv]   fold={fold_idx} skipped: preprocess error ({exc})")
                    continue

                X_train = preprocessed["X_train"]
                X_test = preprocessed["X_test"]

                model = model_spec.factory(y_train)

                fold_fit_start = perf_counter()
                # Targeted suppression for known noisy models:
                # - EllipticEnvelope: covariance rank and runtime warnings on high-D data
                # - LogisticRegression: occasional ConvergenceWarning with saga/L1 on small folds
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        message="The covariance matrix associated to your dataset is not full rank",
                        category=UserWarning,
                    )
                    if model_name.startswith("elliptic_envelope"):
                        warnings.filterwarnings("ignore", category=RuntimeWarning)
                    if model_name.startswith("logistic"):
                        warnings.filterwarnings("ignore", category=ConvergenceWarning)
                    if model_spec.model_kind == "anomaly_detector":
                        if model_spec.fit_mode == "pass_only":
                            pass_mask = y_train.values == 0
                            if pass_mask.sum() == 0:
                                _log_progress(f"[cv]   fold={fold_idx} skipped: no pass-class samples")
                                continue
                            model.fit(X_train.iloc[pass_mask])
                        else:
                            model.fit(X_train)
                    else:
                        model.fit(X_train, y_train)
                fold_fit_elapsed = perf_counter() - fold_fit_start

                scores = _get_risk_scores(model, X_test, model_spec)
                preds = (scores >= np.median(scores)).astype(int) if len(scores) > 0 else np.array([])

                oof_scores[(model_name, fs_name)][test_idx] = scores

                ts_series = pd.Series(timestamps)
                train_dates = ts_series.iloc[train_idx].dt.date
                test_dates = ts_series.iloc[test_idx].dt.date

                pr_auc_val = average_precision_score(y_test, scores) if len(np.unique(y_test)) > 1 else np.nan
                roc_auc_val = roc_auc_score(y_test, scores) if len(np.unique(y_test)) > 1 else np.nan
                recall_at_10 = compute_inspection_metrics(y_test, scores).get("recall_at_10pct", np.nan) if len(scores) > 0 and len(np.unique(y_test)) > 1 else np.nan

                _log_progress(
                    f"[cv]   fold={fold_idx} done {fold_fit_elapsed:.1f}s "
                    f"pr_auc={pr_auc_val:.4f} roc_auc={roc_auc_val:.4f} "
                    f"recall@10={recall_at_10:.4f} features={preprocessed['n_features_used']}"
                )

                fold_record = {
                    "model": model_name,
                    "feature_set": fs_name,
                    "fold": fold_idx,
                    "n_splits": actual_n_splits,
                    "model_family": model_spec.family,
                    "model_kind": model_spec.model_kind,
                    "final_eligible": model_spec.final_eligible,
                    "enabled": enabled,
                    "skip_reason": (
                        "optional dependency missing"
                        if not enabled and model_spec.optional_dependency
                        else ""
                    ),
                    "n_features_requested": preprocessed["n_features_requested"],
                    "n_features_used": preprocessed["n_features_used"],
                    "dropped_all_missing_features": preprocessed["dropped_all_missing_features"],
                    "train_start_date": str(train_dates.min()),
                    "train_end_date": str(train_dates.max()),
                    "test_start_date": str(test_dates.min()),
                    "test_end_date": str(test_dates.max()),
                    "train_fails": int(y_train.sum()),
                    "test_fails": int(y_test.sum()),
                    "n_features_selected": len(selected_features),
                    "selected_features": json.dumps(selected_features),
                    "pr_auc": pr_auc_val,
                    "roc_auc": roc_auc_val,
                    "precision": precision_score(y_test, preds, zero_division=0) if len(preds) > 0 else np.nan,
                    "recall": recall_score(y_test, preds, zero_division=0) if len(preds) > 0 else np.nan,
                    "f1": f1_score(y_test, preds, zero_division=0) if len(preds) > 0 else np.nan,
                    "balanced_accuracy": balanced_accuracy_score(y_test, preds) if len(preds) > 0 else np.nan,
                }

                # Add inspection-rate metrics
                if len(scores) > 0 and len(np.unique(y_test)) > 1:
                    inspection = compute_inspection_metrics(y_test, scores)
                    fold_record.update(inspection)

                records.append(fold_record)

            config_elapsed = perf_counter() - config_start
            config_records = [r for r in records if r["model"] == model_name and r["feature_set"] == fs_name]
            mean_pr_auc_so_far = np.nanmean([r["pr_auc"] for r in config_records]) if config_records else np.nan
            _log_progress(
                f"[cv] DONE {config_idx:03d}/{total_configs} model={model_name} "
                f"feature_set={fs_name} elapsed={config_elapsed:.1f}s "
                f"mean_pr_auc_so_far={mean_pr_auc_so_far:.4f}"
            )
            runtime_records.append({
                "model": model_name,
                "feature_set": fs_name,
                "elapsed": config_elapsed,
            })

    pipeline_elapsed = perf_counter() - pipeline_start
    total_folds = len(records)
    _log_progress(f"[cv] COMPLETE configs={config_idx} folds={total_folds} elapsed={pipeline_elapsed/60:.1f}m")
    if runtime_records:
        top_slow = sorted(runtime_records, key=lambda x: x["elapsed"], reverse=True)[:3]
        _log_progress("[cv] SLOWEST CONFIGS")
        for rank, rec in enumerate(top_slow, start=1):
            _log_progress(
                f"[cv]   {rank}. model={rec['model']} feature_set={rec['feature_set']} "
                f"elapsed={rec['elapsed']:.1f}s"
            )

    cv_results = pd.DataFrame(records)

    oof_base = pd.DataFrame(
        {
            "entity_index": np.arange(len(X)),
            "timestamp": timestamps.values,
            "y_true": y.values,
        }
    )
    oof_extra = {
        f"oof_risk_{model_name}_{fs_name}": scores
        for (model_name, fs_name), scores in oof_scores.items()
    }
    if oof_extra:
        oof_df = pd.concat([oof_base, pd.DataFrame(oof_extra)], axis=1)
    else:
        oof_df = oof_base.copy()

    return cv_results, oof_df
