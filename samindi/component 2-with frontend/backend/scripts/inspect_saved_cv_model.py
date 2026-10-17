"""Run this once to verify that best_cv_guidance_model.pkl is a full sklearn Pipeline."""
from pathlib import Path
import joblib

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL = BASE_DIR / "models" / "best_cv_guidance_model.pkl"

model = joblib.load(MODEL)
print("Loaded:", type(model))
print("Has predict:", hasattr(model, "predict"))
if hasattr(model, "steps"):
    print("Pipeline steps:")
    for name, step in model.steps:
        print(" -", name, "=>", type(step))
else:
    print("WARNING: This is not an sklearn Pipeline object.")
    print("Your API expects a pipeline that accepts raw text directly.")
