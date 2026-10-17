import re
from pathlib import Path
from typing import Any, Dict, Optional

import joblib


def clean_cv_text(text: str) -> str:
    cleaned = str(text).lower()
    cleaned = re.sub(r"[^a-zA-Z0-9\s+#.]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class CareerPathModelService:
    """Load and use the trained TF-IDF + classifier pipeline for career-path prediction."""

    def __init__(self, backend_dir: Path):
        self.backend_dir = Path(backend_dir)
        self.model_path = self.backend_dir / "models" / "best_cv_guidance_model.pkl"
        self.result_path = self.backend_dir / "models" / "best_cv_model_result.json"
        self._model: Optional[Any] = None

    def exists(self) -> bool:
        return self.model_path.exists()

    def load(self):
        if self._model is not None:
            return self._model
        if not self.model_path.exists():
            raise FileNotFoundError(f"Career path model not found: {self.model_path}")

        self._model = joblib.load(self.model_path)
        if not hasattr(self._model, "predict"):
            raise RuntimeError("The saved career-path model has no predict() method.")
        return self._model

    def predict(self, cv_text: str) -> str:
        prediction = self.load().predict([clean_cv_text(cv_text)])
        if len(prediction) == 0:
            raise RuntimeError("Career path model returned no prediction.")
        return str(prediction[0])

    def metadata(self) -> Dict[str, object]:
        result: Dict[str, object] = {
            "model_exists": self.exists(),
            "purpose": "career_path_classification",
        }
        if self._model is not None:
            result["model_object"] = type(self._model).__name__
            if hasattr(self._model, "named_steps"):
                result["pipeline_steps"] = list(self._model.named_steps.keys())
        return result
