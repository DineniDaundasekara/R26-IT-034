#!/opt/anaconda3/bin/python3
"""
SKILLVERIFY ML TRAINING PIPELINE - STEP 5: EVALUATE & SELECT BEST MODEL
=======================================================================
Evaluates all trained candidate architectures on the held-out test partition (N = 255):
  • Macro-Averaged F1-Score & Overall Accuracy
  • Expected Calibration Error (ECE) & Brier Probability Loss
  • Per-Class Precision, Recall, F1, and Confusion Matrix
  • Automated Model Selection Logic
  • Serializes Champion Model to backend/models/best_ml_model.joblib
  • Exports metrics to backend/models/ml_models_comparison.json and results/
"""

import os
import sys
import json
import importlib.util
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workspace_root = os.path.dirname(backend_dir)
for p in [backend_dir, workspace_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

from hr_ml.config import (
    MODELS_DIR,
    BEST_MODEL_PATH,
    METRICS_JSON_PATH,
    CLASSES,
    WORKSPACE_ROOT
)
try:
    from training.evaluate_metrics import (
        compute_classification_metrics,
        compute_calibration_metrics
    )
except ImportError:
    try:
        from evaluate_metrics import (
            compute_classification_metrics,
            compute_calibration_metrics
        )
    except ImportError:
        from experiments.evaluate_metrics import (
            compute_classification_metrics,
            compute_calibration_metrics
        )


# Dynamically import train_and_cross_validate from 04_train_models.py
script_dir = os.path.dirname(os.path.abspath(__file__))
train_script_path = os.path.join(script_dir, "04_train_models.py")
spec = importlib.util.spec_from_file_location("step4_module", train_script_path)
step4_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step4_module)
train_and_cross_validate = step4_module.train_and_cross_validate


def evaluate_and_select():
    print("================================================================================")
    print(" [STEP 5/6] HELD-OUT BENCHMARK EVALUATION & MODEL SELECTION")
    print("================================================================================")

    fitted_pipelines, X_test, y_test, cv_results = train_and_cross_validate()
    os.makedirs(MODELS_DIR, exist_ok=True)

    results = {}
    for name, pipeline in fitted_pipelines.items():
        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)
        confidences = [float(np.max(probs)) for probs in y_proba]

        cls_metrics = compute_classification_metrics(list(y_test), list(y_pred))
        cal_metrics = compute_calibration_metrics(list(y_test), list(y_pred), confidences)

        results[name] = {
            "accuracy": cls_metrics["accuracy"],
            "macroF1": cls_metrics["macroF1"],
            "ece": cal_metrics["ece"],
            "brierScore": cal_metrics["brierScore"],
            "perClass": cls_metrics["perClass"],
            "confusionMatrix": cls_metrics["confusionMatrix"]
        }

    # Best Model Selection Criteria (Top Macro-F1, Lowest ECE)
    sorted_models = sorted(
        results.items(),
        key=lambda item: (-item[1]["macroF1"], item[1]["ece"], item[1]["brierScore"])
    )
    best_model_name = sorted_models[0][0]
    best_macro_f1 = results[best_model_name]["macroF1"]
    best_acc = results[best_model_name]["accuracy"]
    best_pipeline = fitted_pipelines[best_model_name]

    print("\n================================================================================")
    print("                       COMPARATIVE BENCHMARK RESULTS")
    print("================================================================================")
    print(f"{'Model Configuration':<45} | {'Accuracy':<10} | {'Macro-F1':<10} | {'ECE Error':<10} | {'Brier':<8}")
    print("-" * 92)
    for name, r in results.items():
        winner_mark = " (WINNER)" if name == best_model_name else ""
        print(f"{name + winner_mark:<45} | {r['accuracy']*100:>8.2f}% | {r['macroF1']:>10.4f} | {r['ece']:>10.4f} | {r['brierScore']:>8.4f}")
    print("-" * 92)

    print(f"\n🏆 CHAMPION MODEL SELECTED: {best_model_name}")
    print(f"   Accuracy: {best_acc*100:.2f}% | Macro-F1: {best_macro_f1:.4f}")

    # Serialize Champion Pipeline Bundle to backend/models/
    model_bundle = {
        "model_name": best_model_name,
        "macro_f1": best_macro_f1,
        "accuracy": best_acc,
        "classes": CLASSES,
        "pipeline": best_pipeline,
        "metrics": results[best_model_name],
        "cross_validation_scores": cv_results
    }
    joblib.dump(model_bundle, BEST_MODEL_PATH)
    print(f"  ✓ Serialized Model Pipeline to: {BEST_MODEL_PATH}")

    # Sync model to root results/ as well
    results_dir = os.path.join(WORKSPACE_ROOT, "results")
    os.makedirs(results_dir, exist_ok=True)
    joblib.dump(model_bundle, os.path.join(results_dir, "best_ml_model.joblib"))

    # Save Comparison Metrics JSON
    with open(METRICS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "best_model": best_model_name,
            "best_macro_f1": best_macro_f1,
            "best_accuracy": best_acc,
            "cv_scores": cv_results,
            "models": results
        }, f, indent=2)
    print(f"  ✓ Saved Metrics JSON to:        {METRICS_JSON_PATH}")

    # Sync metrics JSON to root results/
    with open(os.path.join(results_dir, "ml_models_comparison.json"), "w", encoding="utf-8") as f:
        json.dump({
            "best_model": best_model_name,
            "best_macro_f1": best_macro_f1,
            "best_accuracy": best_acc,
            "cv_scores": cv_results,
            "models": results
        }, f, indent=2)

    print(f"\n[Step 5 Complete] Evaluation and Model Selection completed successfully.\n")
    return best_model_name, results


if __name__ == "__main__":
    evaluate_and_select()
