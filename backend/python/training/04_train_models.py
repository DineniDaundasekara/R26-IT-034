#!/opt/anaconda3/bin/python3
"""
SKILLVERIFY ML TRAINING PIPELINE - STEP 4: MODEL TRAINING & 5-FOLD CROSS-VALIDATION
===================================================================================
Defines, builds, and cross-validates 3 supervised machine learning architectures:
  1. Model 1: Multinomial Logistic Regression (L2 regularized, balanced class weights)
  2. Model 2: Random Forest Classifier (200 bagging estimators, max depth 10)
  3. Model 3: Gradient Boosting Classifier (180 boosting stages, learning rate 0.06)
  • Uses ColumnTransformer (TF-IDF for text, StandardScaler for numeric, passthrough for binary)
  • Performs 5-Fold Stratified Cross-Validation on the 80% training partition (N = 1,020).
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workspace_root = os.path.dirname(backend_dir)
for p in [backend_dir, workspace_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

from hr_ml.config import (
    FINAL_DATASET_CSV,
    RANDOM_STATE,
    TEST_SPLIT_RATIO,
    CV_FOLDS
)


def get_preprocessor() -> ColumnTransformer:
    text_features = "context_text"
    numeric_features = [
        "claimed_years",
        "observed_years",
        "tenure_ratio",
        "tech_age_margin",
        "days_since_last_activity",
        "relevant_repos_count",
        "total_repos",
        "observed_languages_bytes"
    ]
    binary_features = [
        "in_resume",
        "has_gh_evidence",
        "package_manifest_matched",
        "is_required"
    ]

    return ColumnTransformer(
        transformers=[
            ("text", TfidfVectorizer(max_features=150, ngram_range=(1, 2)), text_features),
            ("num", StandardScaler(), numeric_features),
            ("bin", "passthrough", binary_features)
        ]
    )


def get_candidate_models() -> Dict[str, Any]:
    return {
        "Model 1 (Multinomial Logistic Regression)": LogisticRegression(
            solver="lbfgs",
            C=1.2,
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_STATE
        ),
        "Model 2 (Random Forest Classifier)": RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=3,
            min_samples_leaf=1,
            class_weight="balanced",
            random_state=RANDOM_STATE
        ),
        "Model 3 (Gradient Boosting Classifier)": GradientBoostingClassifier(
            n_estimators=180,
            learning_rate=0.06,
            max_depth=4,
            subsample=0.90,
            random_state=RANDOM_STATE
        )
    }


def train_and_cross_validate():
    print("================================================================================")
    print(" [STEP 4/6] 5-FOLD STRATIFIED CROSS-VALIDATION & PARALLEL MODEL TRAINING")
    print("================================================================================")

    if not os.path.exists(FINAL_DATASET_CSV):
        print("  • Dataset not found! Generating features first...")
        import subprocess
        script_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.run([sys.executable, os.path.join(script_dir, "03_build_training_features.py")], check=True)

    df_full = pd.read_csv(FINAL_DATASET_CSV)
    labels = df_full["ground_truth_label"].tolist()
    df_features = df_full.drop(columns=["ground_truth_label"])

    # 80/20 Stratified Partitioning
    X_train, X_test, y_train, y_test = train_test_split(
        df_features,
        labels,
        test_size=TEST_SPLIT_RATIO,
        random_state=RANDOM_STATE,
        stratify=labels
    )
    print(f"  ✓ Training Partition:   {len(X_train):,} samples (80% Stratified)")
    print(f"  ✓ Evaluation Partition: {len(X_test):,} samples (20% Stratified)")

    preprocessor = get_preprocessor()
    models = get_candidate_models()
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    cv_results = {}
    fitted_pipelines = {}

    print("\n--- 5-Fold Stratified Cross-Validation Results ---")
    for name, clf in models.items():
        pipe = Pipeline([("preprocessor", preprocessor), ("classifier", clf)])
        scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="f1_macro", n_jobs=1)
        cv_results[name] = {"mean_f1": float(scores.mean()), "std_f1": float(scores.std())}
        print(f"  • {name:<45}: 5-Fold Macro-F1 = {scores.mean():.4f} (± {scores.std():.4f})")

        # Fit on full training set
        pipe.fit(X_train, y_train)
        fitted_pipelines[name] = pipe

    print(f"\n[Step 4 Complete] Cross-validation and training finished successfully.\n")
    return fitted_pipelines, X_test, y_test, cv_results


if __name__ == "__main__":
    train_and_cross_validate()
