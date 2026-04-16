#!/usr/bin/env python3
"""Build mart tables for the manufacturing data quality platform."""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

from src.marts import (
    build_daily_failure_rollup,
    build_daily_yield_trend,
    build_feature_action_summary,
    build_feature_failure_relationship,
    build_feature_groups,
    build_feature_missingness,
    build_feature_priority_index,
    build_label_distribution,
    build_secom_overview,
    build_top_signal_fail_separation,
    build_top_signal_profiles,
    build_model_cv_results,
    build_model_benchmark,
    build_model_threshold_analysis,
    build_final_model_test_results,
    build_model_confusion_summary,
    build_selected_signal_shortlist,
    build_model_registry,
    build_model_feature_importance,
    build_model_threshold_cost_curve,
    build_model_probability_bins,
    build_model_inspection_metrics,
    build_model_feature_selection_summary,
    build_anomaly_model_benchmark,
    build_final_model_inspection_curve,
    build_public_notebook_comparison,
)


def main() -> None:
    print("Building mart.secom_overview...")
    build_secom_overview()
    print("  Built mart.secom_overview")

    print("Building mart.label_distribution...")
    build_label_distribution()
    print("  Built mart.label_distribution")

    print("Building mart.feature_missingness...")
    build_feature_missingness()
    print("  Built mart.feature_missingness")

    print("Building mart.top_signal_fail_separation...")
    build_top_signal_fail_separation()
    print("  Built mart.top_signal_fail_separation")

    print("Building mart.top_signal_profiles...")
    build_top_signal_profiles()
    print("  Built mart.top_signal_profiles")

    print("Building mart.feature_failure_relationship...")
    build_feature_failure_relationship()
    print("  Built mart.feature_failure_relationship")

    print("Building mart.daily_failure_rollup...")
    build_daily_failure_rollup()
    print("  Built mart.daily_failure_rollup")

    print("Building mart.feature_priority_index...")
    build_feature_priority_index()
    print("  Built mart.feature_priority_index")

    print("Building mart.daily_yield_trend...")
    build_daily_yield_trend()
    print("  Built mart.daily_yield_trend")

    print("Building mart.feature_action_summary...")
    build_feature_action_summary()
    print("  Built mart.feature_action_summary")

    print("Building mart.feature_groups...")
    build_feature_groups()
    print("  Built mart.feature_groups")

    print("Building mart.model_cv_results...")
    build_model_cv_results()
    print("  Built mart.model_cv_results")

    print("Building mart.model_benchmark...")
    build_model_benchmark()
    print("  Built mart.model_benchmark")

    print("Building mart.model_threshold_analysis...")
    build_model_threshold_analysis()
    print("  Built mart.model_threshold_analysis")

    print("Building mart.final_model_test_results...")
    build_final_model_test_results()
    print("  Built mart.final_model_test_results")

    print("Building mart.model_confusion_summary...")
    build_model_confusion_summary()
    print("  Built mart.model_confusion_summary")

    print("Building mart.selected_signal_shortlist...")
    build_selected_signal_shortlist()
    print("  Built mart.selected_signal_shortlist")

    print("Building mart.model_registry...")
    build_model_registry()
    print("  Built mart.model_registry")

    print("Building mart.model_feature_importance...")
    build_model_feature_importance()
    print("  Built mart.model_feature_importance")

    print("Building mart.model_threshold_cost_curve...")
    build_model_threshold_cost_curve()
    print("  Built mart.model_threshold_cost_curve")

    print("Building mart.model_probability_bins...")
    build_model_probability_bins()
    print("  Built mart.model_probability_bins")

    print("Building mart.model_inspection_metrics...")
    build_model_inspection_metrics()
    print("  Built mart.model_inspection_metrics")

    print("Building mart.model_feature_selection_summary...")
    build_model_feature_selection_summary()
    print("  Built mart.model_feature_selection_summary")

    print("Building mart.anomaly_model_benchmark...")
    build_anomaly_model_benchmark()
    print("  Built mart.anomaly_model_benchmark")

    print("Building mart.final_model_inspection_curve...")
    build_final_model_inspection_curve()
    print("  Built mart.final_model_inspection_curve")

    print("Building mart.public_notebook_comparison...")
    build_public_notebook_comparison()
    print("  Built mart.public_notebook_comparison")

    print("Mart build complete.")


if __name__ == "__main__":
    main()
