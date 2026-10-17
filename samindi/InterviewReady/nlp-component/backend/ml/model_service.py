from functools import lru_cache

import joblib
import pandas as pd

from .config import MODEL_FILE, MODEL_METADATA_FILE
from .feature_builder import build_numeric_features


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            "The final communication model is not available. "
            "Run training/04_train_models.py first."
        )

    model = joblib.load(MODEL_FILE)
    return model


def predict_communication_level(
    transcript: str,
    audio_path: str,
) -> str:

    pipeline = load_model()

    numeric = build_numeric_features(
        transcript,
        audio_path,
    )

    row = {
        "transcript": transcript,
        **numeric,
    }

    input_frame = pd.DataFrame([row])

    predicted_label = str(
        pipeline.predict(input_frame)[0]
    ).strip().lower()

    display = {
        "poor": "Poor Communication",
        "average": "Average Communication",
        "good": "Good Communication",
        "excellent": "Excellent Communication",
    }

    return display.get(
        predicted_label,
        predicted_label.title(),
    )
