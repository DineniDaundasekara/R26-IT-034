import os
import re
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

# ==========================================================
# PATH SETTINGS
# Run this file from: backend/scripts
# ==========================================================
DATASET_FILE = "../audio/label/interview_dataset.csv"
MODEL_FOLDER = "../models"
MODEL_FILE = "../models/communication_skill_model.pkl"

os.makedirs(MODEL_FOLDER, exist_ok=True)

# ==========================================================
# CHECK DATASET EXISTS
# ==========================================================
if not os.path.exists(DATASET_FILE):
    print("Dataset file not found!")
    print("Expected path:", os.path.abspath(DATASET_FILE))
    print("Please check interview_dataset.csv exists in backend/audio/label/")
    exit()

# ==========================================================
# LOAD DATASET
# ==========================================================
df = pd.read_csv(DATASET_FILE)

print("Dataset loaded successfully!")
print("Total records:", len(df))
print(df.head())

# ==========================================================
# CLEAN TEXT
# ==========================================================
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

df["clean_transcript"] = df["transcript"].apply(clean_text)

# ==========================================================
# FEATURES AND LABEL
# ==========================================================
text_feature = "clean_transcript"

numeric_features = [
    "clarity_score",
    "structure_score",
    "professional_expression_score",
    "final_score"
]

X = df[[text_feature] + numeric_features]
y = df["label"]

# ==========================================================
# MODEL PIPELINE
# ==========================================================
preprocessor = ColumnTransformer(
    transformers=[
        ("text", TfidfVectorizer(max_features=5000, ngram_range=(1, 2)), text_feature),
        ("numeric", StandardScaler(), numeric_features)
    ]
)

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(max_iter=1000))
])

# ==========================================================
# TRAIN MODEL
# ==========================================================
model.fit(X, y)

predictions = model.predict(X)
accuracy = accuracy_score(y, predictions)

print("\n===================================")
print("COMMUNICATION SKILL MODEL TRAINING")
print("===================================")
print("Training Accuracy:", round(accuracy, 4))
print(classification_report(y, predictions, zero_division=0))

# ==========================================================
# SAVE MODEL
# ==========================================================
joblib.dump(model, MODEL_FILE)

print("\nModel trained successfully!")
print("Saved model:", os.path.abspath(MODEL_FILE))