import os
import re
import json
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_FILE = os.path.join(BASE_DIR, "data", "cv_training_dataset.csv")
MODEL_FOLDER = os.path.join(BASE_DIR, "models")

MODEL_FILE = os.path.join(MODEL_FOLDER, "logistic_regression_cv_model.pkl")
RESULT_FILE = os.path.join(MODEL_FOLDER, "logistic_regression_cv_result.json")

os.makedirs(MODEL_FOLDER, exist_ok=True)


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z0-9\s+#.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main():
    print("===================================")
    print("LOGISTIC REGRESSION TRAINING")
    print("===================================")

    if not os.path.exists(DATASET_FILE):
        print("Dataset not found. Run prepare_cv_training_dataset.py first.")
        return

    df = pd.read_csv(DATASET_FILE)
    df = df.dropna(subset=["combined_training_text", "career_path_label"])

    df["clean_training_text"] = df["combined_training_text"].apply(clean_text)

    X = df["clean_training_text"]
    y = df["career_path_label"]

    if y.nunique() < 2:
        print("Training needs at least 2 different career_path_label classes.")
        return

    stratify_value = y if y.value_counts().min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=stratify_value
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=12000,
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True
        )),
        ("classifier", LogisticRegression(
    max_iter=4000,
    class_weight="balanced",
    solver="lbfgs"
))
    ])

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, average="weighted", zero_division=0)
    recall = recall_score(y_test, predictions, average="weighted", zero_division=0)
    f1 = f1_score(y_test, predictions, average="weighted", zero_division=0)

    result = {
        "model_name": "Logistic Regression",
        "model_type": "Supervised NLP CV Career Path Classification Model",
        "task": "Career path guidance from extracted CV text",
        "dataset_file": DATASET_FILE,
        "total_records": int(len(df)),
        "train_records": int(len(X_train)),
        "test_records": int(len(X_test)),
        "input_feature": "combined_training_text",
        "target_label": "career_path_label",
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "classification_report": classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0
        ),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
        "saved_model_path": MODEL_FILE
    }

    joblib.dump(model, MODEL_FILE)

    with open(RESULT_FILE, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)

    print(f"{'model_name':<25} {'accuracy':<10} {'precision':<10} {'recall':<10} {'f1_score':<10}")
    print(f"{'Logistic Regression':<25} {round(accuracy,4):<10} {round(precision,4):<10} {round(recall,4):<10} {round(f1,4):<10}")
    print("\nModel saved:", MODEL_FILE)
    print("Result saved:", RESULT_FILE)


if __name__ == "__main__":
    main()