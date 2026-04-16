#!/usr/bin/env python3
"""Run a random-split comparison benchmark (informational only).

This script produces reference results using random 70/30 split,
explicitly labeled as evaluation_protocol="random_split_reference"
and optionally "random_split_undersampled_reference".
It is NOT used for final model selection.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from src.modeling.data import load_modeling_data
from src.modeling.evaluator import _get_risk_scores
from src.modeling.features import build_feature_sets
from src.modeling.inspection import compute_inspection_metrics
from src.modeling.trainer import MODEL_REGISTRY, is_model_enabled, preprocess_fold, _resolve_feature_set


def _run_comparison_loop(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    feature_sets: dict[str, list[str]],
    static_feature_sets: dict[str, list[str]],
    evaluation_protocol: str,
) -> list[dict]:
    records = []
    for model_name, model_spec in MODEL_REGISTRY.items():
        if not is_model_enabled(model_spec):
            continue
        for fs_name, fs_features in feature_sets.items():
            selected_features, X_train_resolved, _ = _resolve_feature_set(
                fs_name, X_train, y_train, fs_features, static_feature_sets
            )

            if fs_name == "missingness_indicators_keep":
                base = static_feature_sets.get("keep_only", X_train.columns.tolist())
                X_test_resolved = X_test[base].copy()
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
                X_test_resolved = X_test

            if len(selected_features) == 0:
                continue

            try:
                preprocessed = preprocess_fold(
                    X_train_resolved, X_test_resolved, selected_features, model_spec
                )
            except ValueError:
                continue

            X_tr = preprocessed["X_train"]
            X_te = preprocessed["X_test"]

            model = model_spec.factory(y_train)
            if model_spec.model_kind == "anomaly_detector":
                if model_spec.fit_mode == "pass_only":
                    pass_mask = y_train.values == 0
                    if pass_mask.sum() == 0:
                        continue
                    model.fit(X_tr.iloc[pass_mask])
                else:
                    model.fit(X_tr)
            else:
                model.fit(X_tr, y_train)

            test_scores = _get_risk_scores(model, X_te, model_spec)
            test_preds = (test_scores >= np.median(test_scores)).astype(int) if len(test_scores) > 0 else np.array([])

            record = {
                "model": model_name,
                "feature_set": fs_name,
                "evaluation_protocol": evaluation_protocol,
                "n_features": len(preprocessed["X_train"].columns),
                "test_pr_auc": float(average_precision_score(y_test, test_scores)) if len(np.unique(y_test)) > 1 else float("nan"),
                "test_roc_auc": float(roc_auc_score(y_test, test_scores)) if len(np.unique(y_test)) > 1 else float("nan"),
                "test_precision": float(precision_score(y_test, test_preds, zero_division=0)) if len(test_preds) > 0 else float("nan"),
                "test_recall": float(recall_score(y_test, test_preds, zero_division=0)) if len(test_preds) > 0 else float("nan"),
                "test_f1": float(f1_score(y_test, test_preds, zero_division=0)) if len(test_preds) > 0 else float("nan"),
            }

            if len(test_scores) > 0 and len(np.unique(y_test)) > 1:
                inspection = compute_inspection_metrics(y_test, test_scores)
                for k, v in inspection.items():
                    record[k] = v

            records.append(record)
    return records


def main() -> None:
    print("=" * 50)
    print("Public Notebook Comparison (Random Split)")
    print("=" * 50)

    X, y, timestamps = load_modeling_data()
    feature_sets = build_feature_sets()
    feature_sets["top_20_effect"] = []
    feature_sets["top_50_effect"] = []
    feature_sets["top_100_effect"] = []
    feature_sets["correlation_pruned_070"] = []
    feature_sets["correlation_pruned_085"] = []
    feature_sets["top_25_mutual_info"] = []
    feature_sets["top_50_mutual_info"] = []
    feature_sets["top_25_auc_gap"] = []
    feature_sets["top_50_auc_gap"] = []
    feature_sets["missingness_indicators_keep"] = []

    static_feature_sets = {
        k: v for k, v in feature_sets.items()
        if k in ("keep_only", "keep_plus_review")
    }

    # Random 70/30 split (stratify to preserve fail rate)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )

    records = []
    print("Running standard random-split reference ...")
    records.extend(_run_comparison_loop(
        X_train, X_test, y_train, y_test,
        feature_sets, static_feature_sets,
        evaluation_protocol="random_split_reference",
    ))

    # Undersampled reference: downsample pass class to match fail count
    print("Running undersampled random-split reference ...")
    pass_idx = y_train[y_train == 0].index
    fail_idx = y_train[y_train == 1].index
    if len(pass_idx) > len(fail_idx) and len(fail_idx) > 0:
        sampled_pass = pd.Series(np.random.default_rng(42).choice(pass_idx, size=len(fail_idx), replace=False))
        under_idx = pd.Index(np.concatenate([sampled_pass.values, fail_idx.values]))
        X_train_under = X_train.loc[under_idx].reset_index(drop=True)
        y_train_under = y_train.loc[under_idx].reset_index(drop=True)
        records.extend(_run_comparison_loop(
            X_train_under, X_test, y_train_under, y_test,
            feature_sets, static_feature_sets,
            evaluation_protocol="random_split_undersampled_reference",
        ))
    else:
        print("  Skipped undersampled loop: not enough pass-class samples to downsample.")

    artifact_dir = Path("artifacts")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "public_notebook_comparison.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump({"results": records}, f, indent=2, default=str)

    print(f"Saved comparison results to {out_path}")
    print(f"Rows written: {len(records)}")
    print("NOTE: These results use random split and are for reference only.")


if __name__ == "__main__":
    main()
