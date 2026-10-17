"""
SkillVerify Machine Learning & Verification Configuration
=========================================================
Central configuration for system paths, model artefacts, dataset locations,
and research threshold parameters.
"""

import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

# Data Directories
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
if not os.path.exists(RAW_DATA_DIR):
    RAW_DATA_DIR = os.path.join(WORKSPACE_ROOT, "datasets")
PROCESSED_DATA_DIR = DATA_DIR

# Raw Dataset Paths
ESCO_DIR = os.path.join(RAW_DATA_DIR, "04_esco")
GITHUB_ROLES_DIR = os.path.join(RAW_DATA_DIR, "01_github_technical_roles")
GITHUB_EXPERTISE_DIR = os.path.join(RAW_DATA_DIR, "02_github_expertise")
RESUME_CORPUS_DIR = os.path.join(RAW_DATA_DIR, "03_resume_corpus")
FEVER_DIR = os.path.join(RAW_DATA_DIR, "05_fever")
AVERITEC_DIR = os.path.join(RAW_DATA_DIR, "06_averitec")
REPO_QUALITY_DIR = os.path.join(RAW_DATA_DIR, "07_repo_quality")
REPO_QUALITY_CSV = os.path.join(REPO_QUALITY_DIR, "results.csv")



# Processed Dataset Files
FINAL_DATASET_CSV = os.path.join(DATA_DIR, "final_training_dataset.csv")
FINAL_DATASET_JSON = os.path.join(DATA_DIR, "final_training_dataset.json")
PREPROCESSED_CLAIMS_CSV = os.path.join(DATA_DIR, "preprocessed_cleaned_claims.csv")

# Models Directory & Artefacts
MODELS_DIR = os.path.join(BASE_DIR, "models")
BEST_MODEL_PATH = os.path.join(MODELS_DIR, "best_ml_model.joblib")
METRICS_JSON_PATH = os.path.join(MODELS_DIR, "ml_models_comparison.json")

# 4-Way Epistemic Verification Classes
CLASSES = [
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "INSUFFICIENT_EVIDENCE",
    "POTENTIAL_CONTRADICTION"
]

CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(CLASSES)}

# Model Hyperparameters & Training Defaults
RANDOM_STATE = 42
TEST_SPLIT_RATIO = 0.20
CV_FOLDS = 5

# Evidence Thresholds
TENURE_SUPPORTED_RATIO = 0.70       # R >= 0.70 indicates full tenure support
MIN_EVIDENCE_REPOS = 1              # Minimum repo count for public evidence
REFERENCE_YEAR = 2026               # Baseline academic reference year
