#!/usr/bin/env python3
"""Run the full SECOM modeling pipeline end-to-end.

This script is separate from the warehouse build and produces:
    - modeling marts in the mart schema
    - A trained model artifact in artifacts/secom_model.joblib
    - Console summary of results
"""

from __future__ import annotations

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

from rich.console import Console
from rich.table import Table

from src.marts.model_benchmark import build_model_benchmark
from src.marts.model_confusion_summary import build_model_confusion_summary
from src.marts.model_cv_results import build_model_cv_results
from src.marts.model_threshold_analysis import build_model_threshold_analysis
from src.marts.final_model_test_results import build_final_model_test_results
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
from src.modeling.pipeline_runner import get_pipeline_results

console = Console()


def main() -> None:
    console.print("=" * 50, style="bold yellow")
    console.print("SECOM Modeling Pipeline", style="bold yellow")
    console.print("=" * 50, style="bold yellow")

    console.print("\n[step] Running modeling pipeline...")
    results = get_pipeline_results()

    console.print("\n[step] Building modeling marts...")
    build_model_cv_results()
    build_model_benchmark()
    build_model_threshold_analysis()
    build_final_model_test_results()
    build_model_confusion_summary()
    build_selected_signal_shortlist()
    build_model_registry()
    build_model_feature_importance()
    build_model_threshold_cost_curve()
    build_model_probability_bins()
    build_model_inspection_metrics()
    build_model_feature_selection_summary()
    build_anomaly_model_benchmark()
    build_final_model_inspection_curve()
    build_public_notebook_comparison()

    best = results["best_info"]
    threshold = results["threshold"]
    final = results["final_eval"]["results"]
    confusion = results["final_eval"]["confusion"]

    console.print("\n[success] Best model:", style="bold green")
    console.print(f"  Model: {best['model']}")
    console.print(f"  Feature set: {best['feature_set']}")
    console.print(f"  Mean CV PR-AUC: {best['mean_pr_auc']:.4f}")

    console.print("\n[success] Selected threshold:", style="bold green")
    console.print(f"  Threshold: {threshold:.2f}")

    console.print("\n[success] Final test results:", style="bold green")
    test_table = Table(show_header=True, header_style="bold magenta")
    test_table.add_column("Metric")
    test_table.add_column("Value")
    test_table.add_row("PR-AUC", f"{final['test_pr_auc']:.4f}")
    test_table.add_row("ROC-AUC", f"{final['test_roc_auc']:.4f}")
    test_table.add_row("Precision", f"{final['test_precision']:.4f}")
    test_table.add_row("Recall", f"{final['test_recall']:.4f}")
    test_table.add_row("F1", f"{final['test_f1']:.4f}")
    console.print(test_table)

    console.print("\n[success] Test confusion matrix:", style="bold green")
    cm_table = Table(show_header=True, header_style="bold magenta")
    cm_table.add_column("")
    cm_table.add_column("Pred Pass")
    cm_table.add_column("Pred Fail")
    cm_table.add_row("Actual Pass", str(confusion["test_tn"]), str(confusion["test_fp"]))
    cm_table.add_row("Actual Fail", str(confusion["test_fn"]), str(confusion["test_tp"]))
    console.print(cm_table)

    console.print("\n[success] Artifact saved to:", style="bold green")
    console.print(f"  {results['final_eval']['artifact_path']}")

    console.print("\n" + "=" * 50, style="bold yellow")
    console.print("Modeling pipeline complete.", style="bold yellow")
    console.print("=" * 50, style="bold yellow")


if __name__ == "__main__":
    main()
