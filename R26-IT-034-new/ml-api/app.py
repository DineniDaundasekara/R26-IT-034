from fastapi import FastAPI
import joblib
import numpy as np

app = FastAPI()

# Load model and polynomial transformer
model = joblib.load("final_model.pkl")
poly = joblib.load("poly.pkl")

@app.get("/")
def home():
    return {"message": "ML API running"}

@app.post("/predict")
def predict(data: dict):

    try:
        sie = data["SIE_avg"]
        psy = data["PsyCap_avg"]
        comp = data["Comp_avg"]

        sample = np.array([[sie, psy, comp]])

        # Transform to polynomial features
        sample_poly = poly.transform(sample)

        # Predict
        score = model.predict(sample_poly)[0]

        # Level logic
        if score >= 4:
            level = "High"
        elif score >= 3:
            level = "Medium"
        else:
            level = "Low"

        return {
            "score": round(float(score), 2),
            "level": level
        }

    except Exception as e:
        return {"error": str(e)}