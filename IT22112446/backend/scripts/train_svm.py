import os
import re
import json
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

DATASET_FILE = "../audio/label/interview_dataset.csv"
MODEL_FOLDER = "../models"
MODEL_FILE = "../models/svm_model.pkl"
JSON_RESULT_FILE = "../models/svm_result.json"

os.makedirs(MODEL_FOLDER, exist_ok=True)


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


if not os.path.exists(DATASET_FILE):
    print("Dataset file not found:", os.path.abspath(DATASET_FILE))
    exit()

df = pd.read_csv(DATASET_FILE)
df = df.dropna(subset=["transcript", "label"])
df["clean_transcript"] = df["transcript"].apply(clean_text)

text_feature = "clean_transcript"

numeric_features = [
    "clarity_score",
    "structure_score",
    "professional_expression_score"
]

X = df[[text_feature] + numeric_features]
y = df["label"]

preprocessor = ColumnTransformer([
    ("text", TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english"), text_feature),
    ("numeric", StandardScaler(), numeric_features)
])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", SVC(
        kernel="linear",
        probability=True,
        class_weight="balanced",
        random_state=42
    ))
])

can_split = len(df) >= 20 and y.value_counts().min() >= 2

if can_split:
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, average="weighted", zero_division=0)
    recall = recall_score(y_test, predictions, average="weighted", zero_division=0)
    f1 = f1_score(y_test, predictions, average="weighted", zero_division=0)

else:
    print("WARNING: Dataset is small or not balanced enough. Training/testing on full dataset for demo only.")

    model.fit(X, y)
    predictions = model.predict(X)

    accuracy = accuracy_score(y, predictions)
    precision = precision_score(y, predictions, average="weighted", zero_division=0)
    recall = recall_score(y, predictions, average="weighted", zero_division=0)
    f1 = f1_score(y, predictions, average="weighted", zero_division=0)

joblib.dump(model, MODEL_FILE)

result_json = {
    "model_name": "SVM",
    "accuracy": round(float(accuracy), 4),
    "precision": round(float(precision), 4),
    "recall": round(float(recall), 4),
    "f1_score": round(float(f1), 4)
}

with open(JSON_RESULT_FILE, "w", encoding="utf-8") as file:
    json.dump(result_json, file, indent=4)

print("\n===================================")
print("SVM RESULT")
print("===================================")
print(f"{'model_name':<25} {'accuracy':<10} {'precision':<10} {'recall':<10} {'f1_score':<10}")
print(f"{'SVM':<25} {round(float(accuracy), 4):<10} {round(float(precision), 4):<10} {round(float(recall), 4):<10} {round(float(f1), 4):<10}")

print("\nModel saved:", MODEL_FILE)
print("JSON result saved:", JSON_RESULT_FILE)