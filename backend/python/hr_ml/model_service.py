"""
Machine Learning Model Inference Service
====================================================
Provides real-time epistemic state prediction, probability calibration,
and confidence estimation using the serialized winning machine learning model.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from .config import BEST_MODEL_PATH, CLASSES


class MLModelService:
    """
    Service wrapper for the trained Supervised Machine Learning pipeline.
    Loads best_ml_model.joblib and performs multimodal inference.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or BEST_MODEL_PATH
        self.bundle = None
        self.pipeline = None
        self.model_name = None
        self.is_loaded = False
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.bundle = joblib.load(self.model_path)
                self.pipeline = self.bundle.get("pipeline")
                self.model_name = self.bundle.get("model_name", "Trained ML Model")
                self.is_loaded = True
            except Exception as e:
                print(f"[MLModelService] Warning: Failed to load model from {self.model_path}: {e}")
                self.is_loaded = False
        else:
            self.is_loaded = False

    def predict_claim(
        self,
        context_text: str,
        skill_name: str,
        target_role: str,
        claimed_years: float,
        observed_years: float,
        tenure_ratio: float,
        tech_age_margin: float,
        days_since_last_activity: float,
        relevant_repos_count: float,
        total_repos: float,
        observed_languages_bytes: float,
        in_resume: float,
        has_gh_evidence: float,
        package_manifest_matched: float,
        is_required: float
    ) -> Dict[str, Any]:
        """
        Runs ML prediction for a single candidate skill claim.
        """
        if not self.is_loaded or self.pipeline is None:
            return {
                "available": False,
                "predicted_label": None,
                "confidence": 0.0,
                "probabilities": {},
                "model_name": None
            }

        input_df = pd.DataFrame([{
            "context_text": context_text or "",
            "skill_name": skill_name,
            "target_role": target_role,
            "claimed_years": float(claimed_years),
            "observed_years": float(observed_years),
            "tenure_ratio": float(tenure_ratio),
            "tech_age_margin": float(tech_age_margin),
            "days_since_last_activity": float(days_since_last_activity),
            "relevant_repos_count": float(relevant_repos_count),
            "total_repos": float(total_repos),
            "observed_languages_bytes": float(observed_languages_bytes),
            "in_resume": float(in_resume),
            "has_gh_evidence": float(has_gh_evidence),
            "package_manifest_matched": float(package_manifest_matched),
            "is_required": float(is_required)
        }])

        try:
            pred = self.pipeline.predict(input_df)[0]
            proba = self.pipeline.predict_proba(input_df)[0]
            classes = self.pipeline.classes_

            prob_dict = {str(c): float(p) for c, p in zip(classes, proba)}
            confidence = float(np.max(proba))

            return {
                "available": True,
                "predicted_label": str(pred),
                "confidence": confidence,
                "probabilities": prob_dict,
                "model_name": self.model_name
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "predicted_label": None,
                "confidence": 0.0
            }

    def predict_single_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convenience method accepting a dictionary of claim features."""
        return self.predict_claim(
            context_text=claim_data.get("resumeContext", claim_data.get("context_text", "")),
            skill_name=claim_data.get("skillName", claim_data.get("skill_name", "Skill")),
            target_role=claim_data.get("targetRole", claim_data.get("target_role", "Full Stack MERN Developer")),
            claimed_years=claim_data.get("claimedYears", claim_data.get("claimed_years", 1.0)),
            observed_years=claim_data.get("observedYears", claim_data.get("observed_years", 0.0)),
            tenure_ratio=claim_data.get("tenureRatio", claim_data.get("tenure_ratio", 0.0)),
            tech_age_margin=claim_data.get("techAgeMargin", claim_data.get("tech_age_margin", 5.0)),
            days_since_last_activity=claim_data.get("daysSinceLastActivity", claim_data.get("days_since_last_activity", 9999)),
            relevant_repos_count=claim_data.get("relevantProjectsCount", claim_data.get("relevant_repos_count", 0)),
            total_repos=claim_data.get("totalRepos", claim_data.get("total_repos", 5)),
            observed_languages_bytes=claim_data.get("observedLanguagesBytes", claim_data.get("observed_languages_bytes", 50000)),
            in_resume=claim_data.get("inResume", claim_data.get("in_resume", 1)),
            has_gh_evidence=claim_data.get("hasPublicEvidence", claim_data.get("has_gh_evidence", 0)),
            package_manifest_matched=claim_data.get("packageManifestMatched", claim_data.get("package_manifest_matched", 0)),
            is_required=claim_data.get("isRequired", claim_data.get("is_required", 1))
        )



# Singleton Instance
_service_instance = None

def get_ml_model_service() -> MLModelService:
    global _service_instance
    if _service_instance is None:
        _service_instance = MLModelService()
    return _service_instance
