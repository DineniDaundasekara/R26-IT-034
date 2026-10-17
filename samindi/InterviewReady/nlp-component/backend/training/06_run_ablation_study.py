import hashlib
import json
import re
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedGroupKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

from ml.config import FEATURE_TABLE_FILE, PROCESSED_DIR

RANDOM_STATE = 42

def normalize_transcript(text):
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def create_transcript_group(text):
    normalized = normalize_transcript(text)
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]

def build_ablation_pipeline(feature_set: str, numeric_columns: list):
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    if feature_set == "text_only":
        transformer = ColumnTransformer([
            ("tfidf", TfidfVectorizer(max_features=3000, ngram_range=(1, 2), sublinear_tf=True), "transcript")
        ])
    elif feature_set == "audio_only":
        audio_cols = [c for c in numeric_columns if "audio" in c or "speech" in c or "silence" in c or "pause" in c or "speaking" in c or "f0" in c or "energy" in c]
        transformer = ColumnTransformer([
            ("numeric", numeric_pipe, audio_cols)
        ])
    elif feature_set == "text_plus_audio_no_star":
        no_star_cols = [c for c in numeric_columns if not c.startswith("star_")]
        transformer = ColumnTransformer([
            ("tfidf", TfidfVectorizer(max_features=3000, ngram_range=(1, 2), sublinear_tf=True), "transcript"),
            ("numeric", numeric_pipe, no_star_cols)
        ])
    else:  # full_multimodal
        transformer = ColumnTransformer([
            ("tfidf", TfidfVectorizer(max_features=3000, ngram_range=(1, 2), sublinear_tf=True), "transcript"),
            ("numeric", numeric_pipe, numeric_columns)
        ])

    return Pipeline([
        ("features", transformer),
        ("classifier", LinearSVC(C=1.0, random_state=RANDOM_STATE, max_iter=4000))
    ])

def main():
    print("========================================")
    print("RUNNING RESEARCH ABLATION STUDY")
    print("========================================")
    data = pd.read_csv(FEATURE_TABLE_FILE)
    data["transcript_group"] = data["transcript"].apply(create_transcript_group)
    
    non_features = {"audio_file", "audio_path", "label", "transcript", "transcript_group"}
    numeric_cols = [c for c in data.columns if c not in non_features]
    
    X = data[["transcript"] + numeric_cols]
    y = data["label"]
    groups = data["transcript_group"]

    sgkf_test = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    train_idx, test_idx = next(sgkf_test.split(X, y, groups))
    
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    groups_train = groups.iloc[train_idx]

    sgkf_cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    configurations = [
        ("M1_Text_Only (TF-IDF)", "text_only", "Linguistic Text Baseline"),
        ("M2_Audio_Only (Acoustic)", "audio_only", "Acoustic Signal Features Only"),
        ("M3_Text_Plus_Audio (No STAR)", "text_plus_audio_no_star", "Multimodal Without STAR Structure"),
        ("M4_Full_MultiModal_Pipeline (Proposed)", "full_multimodal", "Proposed Multimodal Framework (Acoustic + NLP + STAR)")
    ]

    ablation_results = []

    for name, config_key, desc in configurations:
        print(f"\nEvaluating configuration: {name}...")
        pipe = build_ablation_pipeline(config_key, numeric_cols)
        
        cv_scores = cross_val_score(pipe, X_train, y_train, cv=sgkf_cv, groups=groups_train, scoring="f1_macro")
        cv_macro_f1 = float(np.mean(cv_scores))
        
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        
        test_acc = float(accuracy_score(y_test, y_pred))
        test_macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
        test_precision = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
        test_recall = float(recall_score(y_test, y_pred, average="macro", zero_division=0))

        ablation_results.append({
            "configuration": name,
            "description": desc,
            "cv_macro_f1_mean": round(cv_macro_f1, 4),
            "test_accuracy": round(test_acc, 4),
            "test_macro_f1": round(test_macro_f1, 4),
            "test_macro_precision": round(test_precision, 4),
            "test_macro_recall": round(test_recall, 4)
        })

    ablation_df = pd.DataFrame(ablation_results)
    print("\n========================================")
    print("RESEARCH ABLATION STUDY RESULTS (CHAPTER 5 TABLE)")
    print("========================================")
    print(ablation_df[["configuration", "cv_macro_f1_mean", "test_accuracy", "test_macro_f1"]].to_string(index=False))

    out_json = PROCESSED_DIR / "research_ablation_study.json"
    out_csv = PROCESSED_DIR / "research_ablation_study.csv"
    
    out_json.write_text(json.dumps(ablation_results, indent=2), encoding="utf-8")
    ablation_df.to_csv(out_csv, index=False)
    print(f"\nAblation study results exported to:\n{out_json}\n{out_csv}")

if __name__ == "__main__":
    main()
