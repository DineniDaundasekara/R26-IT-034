import hashlib
import json
import re
import sys
from pathlib import Path

# Add backend directory to sys.path automatically
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import joblib
import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import StratifiedGroupKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

from ml.config import (
    FEATURE_TABLE_FILE,
    MODEL_FILE,
    MODEL_METADATA_FILE,
    RESEARCH_METRICS_FILE,
)

RANDOM_STATE = 42
MAX_CV_FOLDS = 5
NON_FEATURE_COLUMNS = {
    "audio_file",
    "audio_path",
    "label",
    "transcript",
    "transcript_group",
}


def normalize_transcript(text):
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def create_transcript_group(text):
    normalized = normalize_transcript(text)
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]


def make_pipeline(model, numeric_columns):
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    feature_processor = ColumnTransformer(
        transformers=[
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=3000,
                    ngram_range=(1, 2),
                    lowercase=True,
                    sublinear_tf=True,
                    min_df=1,
                ),
                "transcript",
            ),
            ("numeric", numeric_pipeline, numeric_columns),
        ],
        remainder="drop",
        sparse_threshold=0.3,
    )

    return Pipeline([
        ("features", feature_processor),
        ("classifier", model),
    ])


def validate_duplicate_labels(data):
    duplicate_rows = data.groupby("transcript_group").filter(lambda group: len(group) > 1)

    if duplicate_rows.empty:
        print("\nExact duplicate transcripts: 0")
        return

    print(f"\nRows belonging to exact duplicate groups: {len(duplicate_rows)}")
    print(f"Exact duplicate groups: {duplicate_rows['transcript_group'].nunique()}")

    conflicts = duplicate_rows.groupby("transcript_group")["label"].nunique()
    conflict_groups = conflicts[conflicts > 1].index.tolist()
    if conflict_groups:
        print("\nIdentical transcripts with conflicting labels:")
        print(
            data[data["transcript_group"].isin(conflict_groups)][
                ["audio_file", "label", "transcript_group"]
            ].to_string(index=False)
        )
        raise ValueError("Duplicate transcript label conflict detected. Review labels first.")


def calculate_group_folds(y, groups, maximum=5):
    temp = pd.DataFrame({"label": y.values, "group": groups.values})
    unique_groups_per_class = temp.groupby("label")["group"].nunique()
    return min(maximum, int(unique_groups_per_class.min()))


def main():
    print("\n========================================")
    print("COMMUNICATION MODEL TRAINING")
    print("========================================")

    if not FEATURE_TABLE_FILE.exists():
        raise FileNotFoundError(
            f"training_feature_table.csv not found: {FEATURE_TABLE_FILE}\n"
            "Run: python -m training.03_build_training_features"
        )

    data = pd.read_csv(FEATURE_TABLE_FILE)
    required = {"audio_file", "audio_path", "transcript", "label"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

    data = data.dropna(subset=["transcript", "label"]).reset_index(drop=True)
    data["transcript"] = data["transcript"].astype(str).str.strip()
    data["label"] = data["label"].astype(str).str.strip().str.lower()

    allowed = {"poor", "average", "good", "excellent"}
    invalid = data[~data["label"].isin(allowed)]
    if not invalid.empty:
        raise ValueError("Allowed labels are poor, average, good, excellent only.")

    data["transcript_group"] = data["transcript"].apply(create_transcript_group)
    validate_duplicate_labels(data)

    distribution = data["label"].value_counts()
    print("\nCommunication classes:")
    print(distribution)
    print(f"\nTotal interviews: {len(data)}")

    numeric_columns = [
        column
        for column in data.columns
        if column not in NON_FEATURE_COLUMNS
        and pd.api.types.is_numeric_dtype(data[column])
    ]
    if not numeric_columns:
        raise ValueError("No numeric NLP/audio features were found.")

    print(f"\nNumeric NLP/audio features: {len(numeric_columns)}")

    X = data[["transcript"] + numeric_columns].copy()
    y = data["label"].copy()
    groups = data["transcript_group"].copy()

    outer_folds = calculate_group_folds(y, groups, maximum=5)
    if outer_folds < 2:
        raise ValueError("Not enough independent transcript groups for group-aware splitting.")

    print("\nCreating duplicate-safe held-out test split using StratifiedGroupKFold...")
    outer_cv = StratifiedGroupKFold(
        n_splits=outer_folds,
        shuffle=True,
        random_state=RANDOM_STATE,
    )
    train_indices, test_indices = next(outer_cv.split(X, y, groups))

    X_train = X.iloc[train_indices].reset_index(drop=True)
    X_test = X.iloc[test_indices].reset_index(drop=True)
    y_train = y.iloc[train_indices].reset_index(drop=True)
    y_test = y.iloc[test_indices].reset_index(drop=True)
    groups_train = groups.iloc[train_indices].reset_index(drop=True)
    groups_test = groups.iloc[test_indices].reset_index(drop=True)

    if set(groups_train) & set(groups_test):
        raise RuntimeError("Data leakage detected: transcript groups overlap train and test.")

    print(f"\nTraining rows: {len(X_train)}")
    print(f"Test rows: {len(X_test)}")
    print("\nTraining class distribution:")
    print(y_train.value_counts())
    print("\nHeld-out test class distribution:")
    print(y_test.value_counts())

    folds = calculate_group_folds(y_train, groups_train, maximum=MAX_CV_FOLDS)
    if folds < 2:
        raise ValueError("Training data cannot support group-aware cross-validation.")

    print(f"\nUsing {folds}-fold Stratified Group Cross-Validation.")
    cv = StratifiedGroupKFold(
        n_splits=folds,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    candidate_models = {
        "Logistic Regression": LogisticRegression(
            max_iter=5000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "Linear SVM": LinearSVC(
            class_weight="balanced",
            random_state=RANDOM_STATE,
            max_iter=20000,
            tol=1e-4,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=400,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }

    results = {}
    sorted_labels = ["poor", "average", "good", "excellent"]

    for name, classifier in candidate_models.items():
        print("\n----------------------------------------")
        print(f"Training: {name}")
        print("----------------------------------------")

        pipeline = make_pipeline(clone(classifier), numeric_columns)
        cv_scores = cross_val_score(
            pipeline,
            X_train,
            y_train,
            groups=groups_train,
            cv=cv,
            scoring="f1_macro",
            n_jobs=-1,
        )

        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)

        test_macro_f1 = f1_score(
            y_test,
            predictions,
            average="macro",
            zero_division=0,
        )
        test_accuracy = accuracy_score(y_test, predictions)

        results[name] = {
            "cv_macro_f1_scores": [float(score) for score in cv_scores],
            "cv_macro_f1_mean": float(np.mean(cv_scores)),
            "cv_macro_f1_std": float(np.std(cv_scores)),
            "test_macro_f1": float(test_macro_f1),
            "test_accuracy": float(test_accuracy),
            "classification_report": classification_report(
                y_test,
                predictions,
                labels=sorted_labels,
                output_dict=True,
                zero_division=0,
            ),
            "confusion_matrix_labels": sorted_labels,
            "confusion_matrix": confusion_matrix(
                y_test,
                predictions,
                labels=sorted_labels,
            ).tolist(),
        }

        print(f"CV Macro-F1 Mean: {np.mean(cv_scores):.4f}")
        print(f"CV Macro-F1 Std:  {np.std(cv_scores):.4f}")
        print(f"Test Macro-F1:    {test_macro_f1:.4f}")
        print(f"Test Accuracy:    {test_accuracy:.4f}")

    best_name = max(
        results,
        key=lambda model_name: results[model_name]["cv_macro_f1_mean"],
    )

    print("\n========================================")
    print("MODEL SELECTION")
    print("========================================")
    for name in candidate_models:
        print(f"{name}: {results[name]['cv_macro_f1_mean']:.4f}")
    print(f"\nSelected model: {best_name}")
    print("Selection rule: highest mean group-aware CV Macro-F1 on training partition.")

    print("\nRefitting selected model using all labelled interviews...")
    final_pipeline = make_pipeline(clone(candidate_models[best_name]), numeric_columns)
    final_pipeline.fit(X, y)
    joblib.dump(final_pipeline, MODEL_FILE)

    exact_duplicate_rows = int(
        data.duplicated(subset=["transcript_group"], keep=False).sum()
    )

    metadata = {
        "selected_model": best_name,
        "classes": sorted(y.unique().tolist()),
        "numeric_feature_columns": numeric_columns,
        "cross_validation_method": "StratifiedGroupKFold",
        "cross_validation_folds": int(folds),
        "held_out_split_method": "StratifiedGroupKFold",
        "training_rows_total": int(len(data)),
        "research_train_rows": int(len(X_train)),
        "research_test_rows": int(len(X_test)),
        "unique_transcript_groups": int(groups.nunique()),
        "rows_in_exact_duplicate_groups": exact_duplicate_rows,
        "model_selection_metric": "Macro-F1",
        "selection_rule": "Highest mean group-aware cross-validated Macro-F1 on training partition.",
        "candidate_output_policy": (
            "Candidate UI shows category and evidence-grounded guidance only; no confidence, "
            "research accuracy, Macro-F1, or raw feature scores."
        ),
    }
    MODEL_METADATA_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    research_output = {
        "selection_rule": "Highest mean group-aware cross-validated Macro-F1 on the training partition.",
        "validation_design": {
            "held_out_test": (
                "Created using StratifiedGroupKFold so exact duplicate transcripts cannot appear "
                "in both research training and test sets."
            ),
            "cross_validation": f"{folds}-fold StratifiedGroupKFold on the research training partition.",
            "group_definition": "SHA-1 fingerprint of normalized transcript text.",
            "test_set_used_for_model_selection": False,
        },
        "dataset": {
            "total_rows": int(len(data)),
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "unique_transcript_groups": int(groups.nunique()),
            "class_distribution": {
                str(label): int(count)
                for label, count in distribution.items()
            },
        },
        "results": results,
        "selected_model": best_name,
        "selected_model_cv_macro_f1": float(results[best_name]["cv_macro_f1_mean"]),
        "selected_model_test_macro_f1": float(results[best_name]["test_macro_f1"]),
        "selected_model_test_accuracy": float(results[best_name]["test_accuracy"]),
    }
    RESEARCH_METRICS_FILE.write_text(
        json.dumps(research_output, indent=2),
        encoding="utf-8",
    )

    print("\n========================================")
    print("TRAINING COMPLETE")
    print("========================================")
    print(f"\nSelected model:\n{best_name}")
    print(f"\nFinal production model saved to:\n{MODEL_FILE}")
    print(f"\nModel metadata saved to:\n{MODEL_METADATA_FILE}")
    print(f"\nResearch metrics saved to:\n{RESEARCH_METRICS_FILE}")
    print("\nResearch metrics are not returned to candidates.")


if __name__ == "__main__":
    main()
