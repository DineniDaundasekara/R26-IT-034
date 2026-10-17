"""Employability Simulator prediction engine.

Ported from three standalone Flask/FastAPI demo prototypes (phase1_demo,
phase2_demo, phase3_demo backends) into one importable, config-driven service
so it can run inside the unified Career Intelligence Platform FastAPI app.

Each phase predicts a continuous employability score (1-5) from a frozen,
validated regression/classification model trained on a different predictor
domain: internship experience (Phase 1, XGBoost), competence (Phase 2, Linear
Regression), and psychological capital (Phase 3, ElasticNet).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import pandas as pd


def guidance_level(score: float) -> str:
    if score >= 4:
        return "Strong"
    if score >= 3:
        return "Developing"
    return "Needs Improvement"


# Development priority target. A construct already at or above this score
# is not treated as a gap. The gain is the frozen model's change when that
# one construct is raised to the target and every other construct stays put.
IMPROVEMENT_TARGET = 4.0
GAIN_EPSILON = 0.0001


class EmployabilityPhaseService:
    """Loads one frozen phase model and runs its construct-scoring + prediction pipeline."""

    def __init__(
        self,
        phase_id: str,
        phase_label: str,
        relationship: str,
        model_path: Any,
        model_type: str,
        model_features: List[str],
        item_labels: Dict[str, str],
        construct_items: Dict[str, List[str]],
        construct_labels: Dict[str, str],
        action_library: Dict[str, str],
        target_field: str,
        preprocessing: Optional[str] = None,
        improvement_by_construct: bool = False,
    ):
        self.phase_id = phase_id
        self.phase_label = phase_label
        self.relationship = relationship
        if isinstance(model_path, (list, tuple)):
            self.model_paths = [Path(p) for p in model_path]
        else:
            self.model_paths = [Path(model_path)]
        self.model_path = self.model_paths[0]
        self.model_type = model_type
        self.model_features = model_features
        self.item_labels = item_labels
        self.construct_items = construct_items
        self.construct_labels = construct_labels
        self.action_library = action_library
        self.target_field = target_field
        self.preprocessing = preprocessing
        # Phase 1 keys development guidance off the construct (4 actions);
        # Phases 2/3 key it off the individual item (10-12 actions).
        self.improvement_by_construct = improvement_by_construct

        self._model = None
        self._load_error: Optional[str] = None

    def _resolve_model_path(self) -> Optional[Path]:
        for p in self.model_paths:
            if p.exists():
                return p
        return None

    def exists(self) -> bool:
        return self._resolve_model_path() is not None

    def load(self):
        if self._model is not None or self._load_error:
            return
        resolved = self._resolve_model_path()
        if not resolved:
            self._load_error = f"Model not found in candidate paths: {[str(p) for p in self.model_paths]}"
            return
        self.model_path = resolved
        try:
            self._model = joblib.load(resolved)
        except Exception as exc:
            self._load_error = str(exc)

    def health(self) -> Dict[str, Any]:
        self.load()
        resolved = self._resolve_model_path()
        loaded = self._model is not None
        return {
            "status": "ok" if loaded else "error",
            "model": "loaded" if loaded else "unavailable",
            "model_type": self.model_type,
            "phase_id": self.phase_id,
            "phase": self.phase_label,
            "relationship": self.relationship,
            "model_path": str(resolved) if resolved else None,
            "feature_count": len(self.model_features),
            "construct_count": len(self.construct_labels),
            "improvement_by_construct": self.improvement_by_construct,
            "error": self._load_error,
        }

    def _calculate_constructs(self, responses: Dict[str, float]) -> Dict[str, float]:
        return {
            feature: sum(responses[item] for item in items) / len(items)
            for feature, items in self.construct_items.items()
        }

    def _build_construct_analysis(self, constructs: Dict[str, float]) -> List[dict]:
        return [
            {
                "construct": self.construct_labels[feature],
                "score": round(constructs[feature], 2),
                "level": guidance_level(constructs[feature]),
            }
            for feature in self.model_features
        ]

    def _build_item_analysis(self, responses: Dict[str, float]) -> List[dict]:
        return [
            {
                "code": code,
                "name": self.item_labels[code],
                "score": float(score),
                "level": guidance_level(score),
            }
            for code, score in responses.items()
        ]

    def _get_strengths(self, item_analysis: List[dict], limit: int = 3) -> List[dict]:
        sorted_items = sorted(item_analysis, key=lambda item: item["score"], reverse=True)
        return [{"name": item["name"], "score": item["score"]} for item in sorted_items[:limit]]

    def _require_model(self):
        self.load()
        if self._load_error or self._model is None:
            raise RuntimeError(self._load_error or f"{self.phase_label} model is unavailable.")

    def _clean_responses(self, responses: Dict[str, float]) -> Dict[str, float]:
        self._require_model()
        expected_codes = set(self.item_labels.keys())
        missing = expected_codes - set(responses.keys())
        if missing:
            raise ValueError(f"Missing responses for: {', '.join(sorted(missing))}")

        clean_responses: Dict[str, float] = {}
        for code in self.item_labels:
            try:
                value = float(responses[code])
            except (TypeError, ValueError):
                raise ValueError(f"Invalid numeric value for '{code}'.")
            if value < 1 or value > 5:
                raise ValueError(f"'{code}' must be between 1 and 5.")
            clean_responses[code] = value
        return clean_responses

    def _predict_score(self, constructs: Dict[str, float]) -> float:
        model_input = pd.DataFrame(
            [[constructs[feature] for feature in self.model_features]],
            columns=self.model_features,
        )
        return float(self._model.predict(model_input)[0])

    def _impact_ranking(self, constructs: Dict[str, float], baseline: float) -> List[dict]:
        """Estimate the score change from raising each construct alone to the target."""
        rows = []
        for feature in self.model_features:
            current = float(constructs[feature])
            if current >= IMPROVEMENT_TARGET:
                simulated = baseline
                gain = 0.0
                already = True
            else:
                modified = dict(constructs)
                modified[feature] = IMPROVEMENT_TARGET
                simulated = self._predict_score(modified)
                gain = simulated - baseline
                already = False
            rows.append(
                {
                    "feature": feature,
                    "name": self.construct_labels[feature],
                    "current_score": round(current, 4),
                    "target_score": IMPROVEMENT_TARGET,
                    "already_at_target": already,
                    "simulated_prediction": round(float(simulated), 4),
                    "expected_gain": round(float(gain), 4),
                }
            )
        rows.sort(key=lambda row: (-row["expected_gain"], row["current_score"], row["name"]))
        return rows

    def _areas_from_impact(
        self, ranking: List[dict], item_analysis: List[dict], baseline: float, limit: int = 3
    ) -> List[dict]:
        areas = []
        for row in ranking:
            if row["expected_gain"] <= GAIN_EPSILON:
                continue
            feature = row["feature"]
            focus_name = None
            focus_code = None
            if self.improvement_by_construct:
                action = self.action_library[feature]
            else:
                item_codes = set(self.construct_items[feature])
                candidates = [item for item in item_analysis if item["code"] in item_codes]
                weakest = min(candidates, key=lambda item: (item["score"], item["code"]))
                focus_name = weakest["name"]
                focus_code = weakest["code"]
                action = self.action_library[focus_code]
            area = {
                "code": feature,
                "name": row["name"],
                "score": round(row["current_score"], 2),
                "action": action,
                "expected_gain": row["expected_gain"],
                "target_score": row["target_score"],
                "simulated_prediction": row["simulated_prediction"],
                "priority_reason": (
                    f"Raising {row['name']} from {row['current_score']:.2f} to "
                    f"{row['target_score']:.2f} increases the predicted employability score by "
                    f"{row['expected_gain']:.2f} (from {baseline:.2f} to {row['simulated_prediction']:.2f})."
                ),
            }
            if focus_name:
                area["focus_item"] = focus_name
                area["focus_item_code"] = focus_code
            areas.append(area)
            if len(areas) == limit:
                break
        return areas

    def predict(self, responses: Dict[str, float]) -> Dict[str, Any]:
        clean_responses = self._clean_responses(responses)
        constructs = self._calculate_constructs(clean_responses)
        prediction = self._predict_score(constructs)

        construct_analysis = self._build_construct_analysis(constructs)
        item_analysis = self._build_item_analysis(clean_responses)
        impact_ranking = self._impact_ranking(constructs, prediction)

        model_info = {
            "model": self.model_type,
            "features": self.model_features,
            "target": self.target_field,
            "status": "Frozen and validated",
        }
        if self.preprocessing:
            model_info["preprocessing"] = self.preprocessing

        payload = {
            "success": True,
            "prediction": {"evs_avg": round(prediction, 4), "scale_min": 1, "scale_max": 5},
            "construct_scores": {key: round(value, 4) for key, value in constructs.items()},
            "construct_analysis": construct_analysis,
            "strengths": self._get_strengths(item_analysis),
            "impact_ranking": impact_ranking,
            "improvement_target": IMPROVEMENT_TARGET,
            "areas_for_improvement": self._areas_from_impact(impact_ranking, item_analysis, prediction),
            "item_analysis": item_analysis,
            "model_info": model_info,
            "note": (
                "Strength and development labels are guidance categories and are not "
                "separate machine-learning classifications."
            ),
        }

        if self.phase_id == "phase1":
            try:
                from phase1_openai_guidance import attach_phase1_recommendations

                attach_phase1_recommendations(
                    payload,
                    model=self._model,
                    constructs=constructs,
                    item_analysis=item_analysis,
                    construct_analysis=construct_analysis,
                    prediction=prediction,
                    item_labels=self.item_labels,
                    construct_items=self.construct_items,
                    construct_labels=self.construct_labels,
                    action_library=self.action_library,
                )
            except Exception as exc:
                print(f"[EMPLOYABILITY] phase1 recommendation failed: {exc}")
                payload["recommendation_source"] = "rule_based_fallback"

        if self.phase_id == "phase2":
            try:
                from phase2_openai_guidance import attach_phase2_recommendations

                attach_phase2_recommendations(
                    payload,
                    model=self._model,
                    constructs=constructs,
                    item_analysis=item_analysis,
                    construct_analysis=construct_analysis,
                    prediction=prediction,
                    item_labels=self.item_labels,
                    construct_items=self.construct_items,
                    construct_labels=self.construct_labels,
                    action_library=self.action_library,
                )
            except Exception as exc:
                print(f"[EMPLOYABILITY] phase2 recommendation failed: {exc}")
                payload["recommendation_source"] = "rule_based_fallback"

        if self.phase_id == "phase3":
            try:
                from phase3_openai_guidance import attach_phase3_recommendations

                attach_phase3_recommendations(
                    payload,
                    model=self._model,
                    constructs=constructs,
                    item_analysis=item_analysis,
                    construct_analysis=construct_analysis,
                    prediction=prediction,
                    item_labels=self.item_labels,
                    construct_items=self.construct_items,
                    construct_labels=self.construct_labels,
                    action_library=self.action_library,
                )
            except Exception as exc:
                print(f"[EMPLOYABILITY] phase3 recommendation failed: {exc}")
                payload["recommendation_source"] = "rule_based_fallback"

        return payload

    def simulate(self, responses: Dict[str, float], overrides: Dict[str, float]) -> Dict[str, Any]:
        """Re-score the frozen model after changing one or more construct averages.

        Survey responses stay as submitted. Overrides replace construct scores
        only for this prediction, so the caller can ask what the employability
        score would be if a construct were higher or lower.
        """
        clean_responses = self._clean_responses(responses)
        if not overrides:
            raise ValueError("Provide at least one construct score to change.")

        unknown = [key for key in overrides if key not in self.model_features]
        if unknown:
            expected = ", ".join(self.model_features)
            raise ValueError(f"Unknown construct: {', '.join(unknown)}. Expected: {expected}.")

        constructs = self._calculate_constructs(clean_responses)
        baseline = self._predict_score(constructs)
        modified = dict(constructs)
        changes = []
        for feature, raw in overrides.items():
            try:
                value = float(raw)
            except (TypeError, ValueError):
                raise ValueError(f"Invalid numeric value for '{feature}'.")
            if value < 1 or value > 5:
                raise ValueError(f"'{feature}' must be between 1 and 5.")
            changes.append(
                {
                    "feature": feature,
                    "name": self.construct_labels[feature],
                    "from_score": round(float(constructs[feature]), 4),
                    "to_score": round(value, 4),
                }
            )
            modified[feature] = value

        simulated = self._predict_score(modified)
        return {
            "success": True,
            "baseline_prediction": round(baseline, 4),
            "simulated_prediction": round(simulated, 4),
            "difference": round(simulated - baseline, 4),
            "scale_min": 1,
            "scale_max": 5,
            "changes": changes,
            "construct_scores": {feature: round(modified[feature], 4) for feature in self.model_features},
            "note": (
                "The simulated score is a new prediction from the same frozen model. "
                "The original responses are not changed."
            ),
        }


# ============================================================================
# PHASE 1 — Internship Experience → Employability (XGBoost)
# ============================================================================

PHASE1_ITEM_LABELS = {
    "SIE1": "I had a clear understanding of the purpose of my internship.",
    "SIE2": "I gained the knowledge expected during my internship.",
    "SIE3": "I understood the standards and expectations of work during my internship.",
    "SIE4": "I had a clear understanding of the tasks assigned to me.",
    "SIE5": "My educational institution helped me prepare for finding an internship.",
    "SIE6": "My academic lectures and professor supported me in completing internship assignments and projects.",
    "SIE7": "I was treated with respect and professionalism during my internship.",
    "SIE8": "My internship supervisor was available whenever I needed guidance.",
    "SIE9": "My supervisor shared useful experiences and advice to help me solve workplace problems.",
    "SIE10": "My supervisor regularly provided constructive feedback on my performance.",
    "SIE11": "My internship improved my future career opportunities.",
    "SIE12": "I participated in challenging projects that enhanced my career development.",
}

PHASE1_CONSTRUCT_ITEMS = {
    "Clear_Objectives": ["SIE1", "SIE2", "SIE3", "SIE4"],
    "School_Support": ["SIE5", "SIE6"],
    "Workplace_Environment": ["SIE7", "SIE8", "SIE9", "SIE10"],
    "Career_Development": ["SIE11", "SIE12"],
}

PHASE1_CONSTRUCT_LABELS = {
    "Clear_Objectives": "Clear Objectives",
    "School_Support": "School Support",
    "Workplace_Environment": "Workplace Environment",
    "Career_Development": "Career Development",
}

PHASE1_ACTION_LIBRARY = {
    "Clear_Objectives": "Discuss internship goals and expected outcomes with the supervisor.",
    "School_Support": "Schedule regular discussions with the academic internship supervisor.",
    "Workplace_Environment": "Request regular and constructive feedback from the workplace supervisor.",
    "Career_Development": "Participate in challenging projects that build industry-relevant experience.",
}


# ============================================================================
# PHASE 2 — Competence → Employability (Linear Regression)
# ============================================================================

PHASE2_ITEM_LABELS = {
    "C1": "Adaptability to Changing Situations and Demands",
    "C2": "Communication and Interaction with Diverse Groups",
    "C3": "Project Planning, Organisation and Execution",
    "C4": "Leadership",
    "C5": "Reasoning and Decision Making",
    "C6": "Communication and Collaboration",
    "C7": "Creativity and Innovation",
    "C8": "Information Access and Evaluation",
    "C9": "Media Communication",
    "C10": "Media Analysis and Creation",
}

PHASE2_CONSTRUCT_ITEMS = {
    "LifeCareer_avg": ["C1", "C2", "C3", "C4"],
    "LearningInnovation_avg": ["C5", "C6", "C7"],
    "ITMedia_avg": ["C8", "C9", "C10"],
}

PHASE2_CONSTRUCT_LABELS = {
    "LifeCareer_avg": "Life & Career Skills",
    "LearningInnovation_avg": "Learning & Innovation Skills",
    "ITMedia_avg": "IT & Media Skills",
}

PHASE2_ACTION_LIBRARY = {
    "C1": "Practice adapting to unexpected situations by solving short scenario-based workplace problems.",
    "C2": "Participate in group discussions with people from different backgrounds and practice active listening.",
    "C3": "Plan a small project using objectives, tasks, responsibilities, deadlines and expected outcomes.",
    "C4": "Take responsibility for coordinating a small team activity and practice delegation and decision-making.",
    "C5": "Practice structured problem solving by identifying a problem, comparing alternatives and explaining your decision.",
    "C6": "Practice presenting ideas clearly and collaborating with others during team-based activities.",
    "C7": "Generate multiple solutions for a common problem and evaluate which solution is most practical.",
    "C8": "Practice finding reliable information from multiple sources and evaluating its credibility.",
    "C9": "Practice communicating professional information through presentations, reports and digital media.",
    "C10": "Analyze digital or media content critically and practice creating clear professional content.",
}


# ============================================================================
# PHASE 3 — Psychological Capital → Employability (ElasticNet)
# ============================================================================

PHASE3_ITEM_LABELS = {
    "PsyCap1": "I can find various ways to overcome obstacles that arise during my studies.",
    "PsyCap2": "I realize that different approaches can be used to overcome the problems I face in my studies.",
    "PsyCap3": "I am committed to doing my best and working hard to achieve the goals I set.",
    "PsyCap4": "I have high hopes that I can succeed in my learning activities.",
    "PsyCap5": "I am optimistic that the time and effort I invest now will bring positive results in the future.",
    "PsyCap6": "I tend to identify positive lessons from my learning experiences, whether they involve success or failure.",
    "PsyCap7": "I can identify and analyze problems that arise during my learning activities.",
    "PsyCap8": "When I receive low grades, I try to identify the reasons and find ways to improve.",
    "PsyCap9": "I understand that failure can happen, and I am able to recover and continue working toward long-term success.",
    "PsyCap10": "I believe that I can successfully complete difficult tasks.",
    "PsyCap11": "I am confident enough to ask my teacher or lecturer for help when I have difficulty completing an assignment.",
    "PsyCap12": "I am confident that I can make a meaningful and useful contribution to others using my abilities.",
}

PHASE3_CONSTRUCT_ITEMS = {
    "Hope_avg": ["PsyCap1", "PsyCap2", "PsyCap3"],
    "Optimism_avg": ["PsyCap4", "PsyCap5", "PsyCap6"],
    "Resilience_avg": ["PsyCap7", "PsyCap8", "PsyCap9"],
    "SelfEfficacy_avg": ["PsyCap10", "PsyCap11", "PsyCap12"],
}

PHASE3_CONSTRUCT_LABELS = {
    "Hope_avg": "Hope",
    "Optimism_avg": "Optimism",
    "Resilience_avg": "Resilience",
    "SelfEfficacy_avg": "Self-Efficacy",
}

PHASE3_ACTION_LIBRARY = {
    "PsyCap1": "When you face a difficult task, write down two or three possible ways to handle it before choosing the best option.",
    "PsyCap2": "If your first solution does not work, try another method or ask someone experienced for a different perspective.",
    "PsyCap3": "Break an important career or work goal into small weekly tasks and check your progress regularly.",
    "PsyCap4": "Keep a short record of skills, tasks or responsibilities you are improving so you can see your progress clearly.",
    "PsyCap5": "Choose one professional-development activity and connect it with a future career or work goal.",
    "PsyCap6": "After an important task, note one thing that worked well and one thing you would improve next time.",
    "PsyCap7": "Before reacting to a difficult situation, identify the main problem, possible causes and the information you need.",
    "PsyCap8": "When a task does not go as planned, identify the main reason and choose one clear improvement for your next attempt.",
    "PsyCap9": "After a setback, decide on one realistic next step and restart instead of leaving the task unfinished.",
    "PsyCap10": "Choose a slightly challenging task, complete it step by step and recognise what you managed successfully.",
    "PsyCap11": "When you are stuck, ask a manager, mentor, colleague, lecturer or trainer for specific guidance instead of waiting too long.",
    "PsyCap12": "Look for a small task where you can use one of your strongest skills to help your team, project or workplace.",
}


def build_phase_services(backend_dir: Path) -> Dict[str, EmployabilityPhaseService]:
    backend_dir = Path(backend_dir)
    models_dir = backend_dir / "models"

    phase1 = EmployabilityPhaseService(
        phase_id="phase1",
        phase_label="Phase 01",
        relationship="Internship Experience → Employability",
        model_path=[
            models_dir / "phase1_employability_model.joblib",
            models_dir / "final_employability_model.joblib",
            models_dir / "final_employability_random_forest.joblib",
            models_dir / "tuned_random_forest_research_model.joblib",
            models_dir / "phase1" / "phase1_employability_model.joblib",
            models_dir / "phase1" / "final_employability_model.joblib",
        ],
        model_type="XGBoost",
        model_features=["Clear_Objectives", "School_Support", "Workplace_Environment", "Career_Development"],
        item_labels=PHASE1_ITEM_LABELS,
        construct_items=PHASE1_CONSTRUCT_ITEMS,
        construct_labels=PHASE1_CONSTRUCT_LABELS,
        action_library=PHASE1_ACTION_LIBRARY,
        target_field="Employability_Score",
        improvement_by_construct=True,
    )

    phase2 = EmployabilityPhaseService(
        phase_id="phase2",
        phase_label="Phase 02",
        relationship="Competence → Employability",
        model_path=[
            models_dir / "phase2" / "phase2_competence_final_model.pkl",
            models_dir / "phase2_competence_final_model.pkl",
            models_dir / "phase2_competence_model.pkl",
            models_dir / "phase2" / "phase2_competence_model.pkl",
            models_dir / "phase2_competence" / "phase2_competence_model.pkl",
            models_dir / "phase2" / "model.pkl",
            models_dir / "phase2_competence" / "model.pkl",
        ],
        model_type="Linear Regression",
        model_features=["LifeCareer_avg", "LearningInnovation_avg", "ITMedia_avg"],
        item_labels=PHASE2_ITEM_LABELS,
        construct_items=PHASE2_CONSTRUCT_ITEMS,
        construct_labels=PHASE2_CONSTRUCT_LABELS,
        action_library=PHASE2_ACTION_LIBRARY,
        target_field="EVS_avg",
        preprocessing="StandardScaler",
        improvement_by_construct=False,
    )

    phase3 = EmployabilityPhaseService(
        phase_id="phase3",
        phase_label="Phase 03",
        relationship="Psychological Capital → Employability",
        model_path=[
            models_dir / "phase3" / "phase3_psycap_selected_model.pkl",
            models_dir / "phase3" / "phase3_psycap_model.pkl",
            models_dir / "phase3_psycap_model.pkl",
            models_dir / "phase3" / "model.pkl",
        ],
        model_type="ElasticNet",
        model_features=["Hope_avg", "Optimism_avg", "Resilience_avg", "SelfEfficacy_avg"],
        item_labels=PHASE3_ITEM_LABELS,
        construct_items=PHASE3_CONSTRUCT_ITEMS,
        construct_labels=PHASE3_CONSTRUCT_LABELS,
        action_library=PHASE3_ACTION_LIBRARY,
        target_field="EVS_avg",
        preprocessing="StandardScaler",
        improvement_by_construct=False,
    )

    return {"phase1": phase1, "phase2": phase2, "phase3": phase3}
