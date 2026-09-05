"""
Scientific Evaluation Metrics Module
Computes Macro-F1, Per-Class Precision/Recall, Normalized Confusion Matrix,
Expected Calibration Error (ECE), and Brier Score.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from collections import defaultdict


CLASSES = ["SUPPORTED", "PARTIALLY_SUPPORTED", "INSUFFICIENT_EVIDENCE", "POTENTIAL_CONTRADICTION"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}


def compute_classification_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, Any]:
    """
    Computes rigorous classification metrics (Macro-F1, Precision, Recall, Confusion Matrix)
    for the 4-way consistency verification task.
    """
    n_classes = len(CLASSES)
    confusion = np.zeros((n_classes, n_classes), dtype=int)

    for yt, yp in zip(y_true, y_pred):
        if yt in CLASS_TO_IDX and yp in CLASS_TO_IDX:
            confusion[CLASS_TO_IDX[yt]][CLASS_TO_IDX[yp]] += 1

    per_class = {}
    f1_list = []
    
    for i, c_name in enumerate(CLASSES):
        tp = confusion[i, i]
        fp = np.sum(confusion[:, i]) - tp
        fn = np.sum(confusion[i, :]) - tp
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        f1_list.append(f1)
        per_class[c_name] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": int(np.sum(confusion[i, :]))
        }

    macro_f1 = float(np.mean(f1_list))
    accuracy = float(np.trace(confusion) / np.sum(confusion)) if np.sum(confusion) > 0 else 0.0

    return {
        "macroF1": round(macro_f1, 4),
        "accuracy": round(accuracy, 4),
        "perClass": per_class,
        "confusionMatrix": confusion.tolist(),
        "classes": CLASSES
    }


def compute_calibration_metrics(
    y_true: List[str],
    y_pred: List[str],
    confidences: List[float],
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    Calculates Expected Calibration Error (ECE) and Brier Score.
    ECE measures the alignment between confidence probabilities and actual correctness.
    """
    correct = [1 if yt == yp else 0 for yt, yp in zip(y_true, y_pred)]
    n_samples = len(correct)
    
    if n_samples == 0:
        return {"ece": 0.0, "brierScore": 0.0}

    # Brier Score (1-correctness confidence penalty)
    brier = np.mean([(conf - corr) ** 2 for conf, corr in zip(confidences, correct)])

    # ECE Binning
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bins[i]
        bin_upper = bins[i + 1]
        
        in_bin = [
            j for j in range(n_samples)
            if bin_lower <= confidences[j] < bin_upper or (i == n_bins - 1 and confidences[j] == 1.0)
        ]
        
        if len(in_bin) > 0:
            bin_acc = np.mean([correct[j] for j in in_bin])
            bin_conf = np.mean([confidences[j] for j in in_bin])
            bin_weight = len(in_bin) / n_samples
            ece += bin_weight * abs(bin_acc - bin_conf)

    return {
        "ece": round(float(ece), 4),
        "brierScore": round(float(brier), 4)
    }
