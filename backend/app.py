from pathlib import Path
from datetime import datetime, timezone
import json
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI
from pymongo import DESCENDING, MongoClient
from bson import ObjectId
import joblib
import pandas as pd

from history_store import (
    delete_assessment,
    get_assessment,
    init_db,
    list_assessments,
    save_assessment,
)


load_dotenv(Path(__file__).resolve().parent / ".env")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

try:
    init_db()
except Exception as history_init_error:  # noqa: BLE001
    print(f"History database init warning: {history_init_error}")

MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
MONGODB_DB_NAME = "career_framework_db"
MONGODB_COLLECTION_NAME = "career_safety_assessments"

mongo_client = None
assessments_collection = None

try:
    if MONGODB_URI:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Trigger a lightweight connectivity check at startup.
        mongo_client.admin.command("ping")
        assessments_collection = mongo_client[MONGODB_DB_NAME][MONGODB_COLLECTION_NAME]
        print("MongoDB connected: career_framework_db.career_safety_assessments")
    else:
        print("MongoDB warning: MONGODB_URI is missing. Assessment cloud save is disabled.")
except Exception as mongo_init_error:  # noqa: BLE001
    mongo_client = None
    assessments_collection = None
    print(f"MongoDB init warning: {mongo_init_error}")

MAIN_MODEL_PATH = "career_risk_model.pkl"
MAIN_ENCODERS_PATH = "career_risk_label_encoders.pkl"
AUX_MODELS_PATH = "simplified_auxiliary_indicator_models.pkl"
ALL_ENCODERS_PATH = "simplified_all_label_encoders.pkl"
AUX_COLUMNS_PATH = "simplified_auxiliary_input_columns.pkl"
OPENAI_MODEL = "gpt-4o-mini"

DECISION_SUPPORT_NOTE = (
    "This system provides explainable career risk estimation for decision-support "
    "purposes. It does not predict job loss or make final career decisions."
)

MODEL_PREDICTION_NOTE = (
    "This is the only overall career risk prediction from the main Random Forest model. "
    "Supporting indicators are system-derived or AI-generated guidance."
)

LEARNING_SCORE = {
    "0 hours": 0,
    "1-3 hours": 1,
    "4-7 hours": 2,
    "8+ hours": 3,
}

SKILL_UPDATE_SCORE = {
    "Rarely": 0,
    "Occasionally": 1,
    "Regularly": 2,
    "Continuously": 3,
}

EXPERIENCE_SCORE = {
    "0-2 years": 1,
    "3-5 years": 2,
    "6-10 years": 3,
    "10+ years": 4,
}

STRATEGY_SCORE = {
    "No clear strategy": 0,
    "Move to management roles": 1,
    "Multi-skill generalization": 2,
    "Deep specialization": 2,
}

AUTOMATION_TO_AI_REPLACEABILITY = {"Low": 1, "Medium": 3, "High": 5}
DOMAIN_TO_STABILITY = {"Low": 2, "Medium": 3, "High": 5}
TREND_LEVEL_TO_MARKET = {
    "Declining": "Slight decrease",
    "Stable": "No change",
    "Growing": "Increase",
}

STABILITY_DISPLAY_TO_MAIN = {
    "Continuous learning": "Experience with AI tools",
    "Industry certifications": "Industry certifications",
    "Limited career planning": "None of Above",
    "Skill diversification": "Cross-functional skills",
}

ROLE_SKILL_HINTS = {
    "Quality Assurance / Testing": (
        "test automation, Selenium, Playwright, API testing, CI/CD, AI testing tools"
    ),
    "Software Development / Engineering": (
        "system design, cloud basics, DevOps, clean architecture, AI-assisted development"
    ),
    "Cloud & DevOps": (
        "Kubernetes, Docker, Terraform, cloud security, monitoring, CI/CD pipelines"
    ),
    "Cyber Security": (
        "SIEM, threat detection, cloud security, incident response, security certifications"
    ),
    "Data Science / AI / ML": (
        "MLOps, data engineering, model deployment, cloud AI services, responsible AI"
    ),
    "UI/UX & Product Design": (
        "UX research, accessibility, design systems, product thinking, usability testing"
    ),
    "Project Management / Business Analysis": (
        "agile analytics, stakeholder communication, product strategy, data literacy, "
        "AI tools for project management"
    ),
}

GUIDANCE_KEYS = [
    "explainableRecommendation",
    "mainRiskyAreas",
    "careerStrengths",
    "industryStabilityInsight",
    "skillTransferabilityInsight",
    "adaptabilityReadinessInsight",
    "recommendedNextSteps",
    "whyThisResult",
    "recommendationMapping",
    "careerResilienceActionPlan",
]

ACTION_PLAN_KEYS = [
    "summary",
    "actionPriorityLevel",
    "thirtyDayPlan",
    "sixtyDayPlan",
    "ninetyDayPlan",
    "prioritySkillsToImprove",
    "suggestedLearningFocus",
    "careerStrategyAdjustment",
    "riskReductionActions",
    "progressTrackingSuggestions",
]

ACTION_PLAN_LIST_KEYS = [
    "thirtyDayPlan",
    "sixtyDayPlan",
    "ninetyDayPlan",
    "prioritySkillsToImprove",
    "suggestedLearningFocus",
    "careerStrategyAdjustment",
    "riskReductionActions",
    "progressTrackingSuggestions",
]

REQUIRED_FIELDS = [
    "role",
    "years_experience",
    "tech_stack_change",
    "weekly_learning_time",
    "switch_confidence",
    "career_strategy",
    "skill_update_frequency",
]

NUMERIC_INPUT_FIELDS = ["tech_stack_change", "switch_confidence"]
MAIN_NUMERIC_FIELDS = ["tech_stack_change", "ai_replaceability", "domain_stability", "switch_confidence"]


def load_artifacts():
    main_model = joblib.load(MAIN_MODEL_PATH)
    main_encoders = joblib.load(MAIN_ENCODERS_PATH)
    aux_models = joblib.load(AUX_MODELS_PATH)
    all_encoders = joblib.load(ALL_ENCODERS_PATH)
    aux_columns = joblib.load(AUX_COLUMNS_PATH)
    if not isinstance(aux_models, dict):
        raise ValueError("Auxiliary models artifact must be a dictionary.")
    if not isinstance(all_encoders, dict) or not isinstance(main_encoders, dict):
        raise ValueError("Label encoder artifacts must be dictionaries.")
    if not isinstance(aux_columns, list):
        raise ValueError("Auxiliary input columns artifact must be a list.")
    return main_model, main_encoders, aux_models, all_encoders, aux_columns


try:
    (
        main_model,
        main_encoders,
        aux_models,
        all_encoders,
        aux_columns,
    ) = load_artifacts()
except Exception as exc:
    main_model = None
    main_encoders = {}
    aux_models = {}
    all_encoders = {}
    aux_columns = []
    startup_error = str(exc)
else:
    startup_error = None


def decode_with_encoder(encoders, key, pred_value):
    encoder = encoders.get(key)
    if encoder is None:
        return str(pred_value)
    try:
        return str(encoder.inverse_transform([int(pred_value)])[0])
    except Exception:
        normalized = str(pred_value).strip()
        return normalized


def decode_risk_label(pred_value, encoders):
    decoded = decode_with_encoder(encoders, "career_risk_level", pred_value)
    normalized = str(decoded).strip().lower()
    alias_map = {
        "0": "Low Risk",
        "1": "Moderate Risk",
        "2": "High Risk",
        "low": "Low Risk",
        "low risk": "Low Risk",
        "moderate": "Moderate Risk",
        "moderate risk": "Moderate Risk",
        "medium": "Moderate Risk",
        "high": "High Risk",
        "high risk": "High Risk",
    }
    return alias_map.get(normalized, str(decoded))


def scale_label(value):
    if value <= 2:
        return "Low"
    if value == 3:
        return "Medium"
    return "High"


def learning_activity_label(weekly_learning_time):
    mapping = {
        "0 hours": "Low",
        "1-3 hours": "Low",
        "4-7 hours": "Medium",
        "8+ hours": "High",
    }
    return mapping.get(str(weekly_learning_time).strip(), str(weekly_learning_time))


def skill_update_behavior_label(frequency):
    mapping = {
        "Continuously": "Continuous",
        "Regularly": "Regular",
        "Occasionally": "Occasional",
        "Rarely": "Rare",
    }
    return mapping.get(str(frequency).strip(), str(frequency))


def encode_categorical(encoders, key, value):
    if key not in encoders:
        return value
    encoder = encoders[key]
    as_text = str(value).strip()
    if as_text not in encoder.classes_:
        allowed = ", ".join(map(str, encoder.classes_))
        raise ValueError(
            f"Invalid categorical value for '{key}': '{value}'. Allowed values: {allowed}"
        )
    return int(encoder.transform([as_text])[0])


def validate_payload(payload):
    if not isinstance(payload, dict):
        return False, "Request body must be a valid JSON object.", None

    missing = [field for field in REQUIRED_FIELDS if field not in payload or payload[field] in ("", None)]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}", None

    sanitized = {field: payload[field] for field in REQUIRED_FIELDS}
    for field in NUMERIC_INPUT_FIELDS:
        try:
            numeric_value = int(float(sanitized[field]))
        except (TypeError, ValueError):
            return False, f"Invalid numeric value for '{field}'. Expected an integer from 1 to 5.", None
        if numeric_value < 1 or numeric_value > 5:
            return False, f"Invalid numeric value for '{field}'. Expected a value from 1 to 5.", None
        sanitized[field] = numeric_value

    return True, None, sanitized


def derive_scores(raw_input):
    learning_score = LEARNING_SCORE.get(str(raw_input["weekly_learning_time"]).strip())
    skill_update_score = SKILL_UPDATE_SCORE.get(str(raw_input["skill_update_frequency"]).strip())
    experience_score = EXPERIENCE_SCORE.get(str(raw_input["years_experience"]).strip())
    strategy_score = STRATEGY_SCORE.get(str(raw_input["career_strategy"]).strip())
    if None in (learning_score, skill_update_score, experience_score, strategy_score):
        raise ValueError("Could not derive numeric scores from one or more practical inputs.")
    adaptability_score = (
        learning_score
        + skill_update_score
        + int(raw_input["tech_stack_change"])
        + int(raw_input["switch_confidence"])
    )
    return {
        "learning_score": learning_score,
        "skill_update_score": skill_update_score,
        "experience_score": experience_score,
        "strategy_score": strategy_score,
        "adaptability_score": adaptability_score,
    }


def derive_stability_indicators(raw_input):
    skill_update = str(raw_input["skill_update_frequency"]).strip()
    weekly_learning = str(raw_input["weekly_learning_time"]).strip()
    strategy = str(raw_input["career_strategy"]).strip()
    if skill_update == "Continuously" or weekly_learning == "8+ hours":
        return "Continuous learning"
    if skill_update == "Regularly":
        return "Industry certifications"
    if strategy == "No clear strategy":
        return "Limited career planning"
    return "Skill diversification"


def predict_auxiliary_levels(raw_input, scores):
    row = {
        "role": encode_categorical(all_encoders, "role", raw_input["role"]),
        "years_experience": encode_categorical(
            all_encoders, "years_experience", raw_input["years_experience"]
        ),
        "tech_stack_change": int(raw_input["tech_stack_change"]),
        "weekly_learning_time": encode_categorical(
            all_encoders, "weekly_learning_time", raw_input["weekly_learning_time"]
        ),
        "switch_confidence": int(raw_input["switch_confidence"]),
        "career_strategy": encode_categorical(
            all_encoders, "career_strategy", raw_input["career_strategy"]
        ),
        "skill_update_frequency": encode_categorical(
            all_encoders, "skill_update_frequency", raw_input["skill_update_frequency"]
        ),
        **scores,
    }

    missing = [col for col in aux_columns if col not in row]
    if missing:
        raise ValueError(f"Auxiliary input is missing columns: {', '.join(missing)}")

    aux_df = pd.DataFrame([row])[aux_columns]
    predicted = {}
    for target_name, estimator in aux_models.items():
        pred = estimator.predict(aux_df)[0]
        predicted[target_name] = decode_with_encoder(all_encoders, target_name, pred)
    return predicted


def build_main_model_row(raw_input, derived):
    stability_for_model = STABILITY_DISPLAY_TO_MAIN.get(
        derived["stabilityIndicators"], derived["stabilityIndicators"]
    )
    return {
        "role": raw_input["role"],
        "years_experience": raw_input["years_experience"],
        "tech_stack_change": raw_input["tech_stack_change"],
        "weekly_learning_time": raw_input["weekly_learning_time"],
        "stability_indicators": stability_for_model,
        "ai_replaceability": derived["aiReplaceability"],
        "domain_stability": derived["domainStability"],
        "job_market_trend": derived["jobMarketTrend"],
        "switch_confidence": raw_input["switch_confidence"],
        "career_strategy": raw_input["career_strategy"],
        "skill_update_frequency": raw_input["skill_update_frequency"],
    }


def encode_main_features(input_data, encoders, feature_names):
    encoded = {}
    for key in feature_names:
        value = input_data[key]
        if key in encoders:
            encoded[key] = encode_categorical(encoders, key, value)
        elif key in MAIN_NUMERIC_FIELDS:
            encoded[key] = int(value)
        else:
            raise ValueError(f"Unexpected main-model field '{key}'.")
    return encoded


def empty_action_plan(summary=None):
    return {
        "summary": summary
        or "Career resilience action plan could not be generated at this time.",
        "actionPriorityLevel": "",
        "thirtyDayPlan": [],
        "sixtyDayPlan": [],
        "ninetyDayPlan": [],
        "prioritySkillsToImprove": [],
        "suggestedLearningFocus": [],
        "careerStrategyAdjustment": [],
        "riskReductionActions": [],
        "progressTrackingSuggestions": [],
    }


def empty_guidance(message):
    return {
        "explainableRecommendation": (
            "AI-generated guidance is currently unavailable. "
            "Please review the model prediction and system-derived indicators."
        ),
        "mainRiskyAreas": [],
        "careerStrengths": [],
        "industryStabilityInsight": "",
        "skillTransferabilityInsight": "",
        "adaptabilityReadinessInsight": "",
        "recommendedNextSteps": [],
        "whyThisResult": [],
        "recommendationMapping": [],
        "careerResilienceActionPlan": empty_action_plan(),
        "generationStatus": "failed",
        "generationMessage": message,
    }


def parse_openai_json(raw_text):
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("Empty OpenAI response.")
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def as_string_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def as_mapping_list(value):
    rows = []
    if not isinstance(value, list):
        return rows
    for item in value:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "riskFactor": str(item.get("riskFactor", "")).strip(),
                "condition": str(item.get("condition", "")).strip(),
                "lackingArea": str(item.get("lackingArea", "")).strip(),
                "recommendation": str(item.get("recommendation", "")).strip(),
            }
        )
    return [row for row in rows if any(row.values())]


def normalize_action_plan(raw_plan):
    if not isinstance(raw_plan, dict):
        return empty_action_plan()

    normalized = {
        "summary": str(raw_plan.get("summary", "")).strip(),
        "actionPriorityLevel": str(raw_plan.get("actionPriorityLevel", "")).strip(),
    }
    for key in ACTION_PLAN_LIST_KEYS:
        normalized[key] = as_string_list(raw_plan.get(key))

    if not normalized["summary"] and not any(normalized[key] for key in ACTION_PLAN_LIST_KEYS):
        return empty_action_plan()
    return normalized


def normalize_guidance(parsed):
    if not isinstance(parsed, dict):
        raise ValueError("OpenAI JSON must be an object.")
    return {
        "explainableRecommendation": str(parsed.get("explainableRecommendation", "")).strip(),
        "mainRiskyAreas": as_string_list(parsed.get("mainRiskyAreas")),
        "careerStrengths": as_string_list(parsed.get("careerStrengths")),
        "industryStabilityInsight": str(parsed.get("industryStabilityInsight", "")).strip(),
        "skillTransferabilityInsight": str(parsed.get("skillTransferabilityInsight", "")).strip(),
        "adaptabilityReadinessInsight": str(parsed.get("adaptabilityReadinessInsight", "")).strip(),
        "recommendedNextSteps": as_string_list(parsed.get("recommendedNextSteps")),
        "whyThisResult": as_string_list(parsed.get("whyThisResult")),
        "recommendationMapping": as_mapping_list(parsed.get("recommendationMapping")),
        "careerResilienceActionPlan": normalize_action_plan(
            parsed.get("careerResilienceActionPlan")
        ),
        "generationStatus": "ok",
        "generationMessage": "",
    }


def generate_ai_guidance(user_profile, model_prediction, indicators):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "your_openai_api_key_here":
        return empty_guidance(
            "AI guidance generation failed: OPENAI_API_KEY is missing. Model prediction and derived indicators are still available."
        )

    role = str(user_profile.get("role", "")).strip()
    role_hint = ROLE_SKILL_HINTS.get(role, "role-relevant technical and transferable skills")
    payload = {
        "userProfile": user_profile,
        "modelPrediction": model_prediction,
        "systemDerivedIndicators": indicators,
        "roleSpecificSkillFocus": role_hint,
    }

    system_prompt = (
        "You generate Section 3 career guidance for a university research prototype on "
        "Career Safety and Industry Stability Analysis. "
        "Return valid JSON only. Do not return markdown. Do not return text outside JSON. "
        "The JSON object must include exactly these top-level keys: "
        + ", ".join(GUIDANCE_KEYS)
        + ". "
        "careerResilienceActionPlan must be an object with exactly these keys: "
        + ", ".join(ACTION_PLAN_KEYS)
        + ". "
        "Use the label actionPriorityLevel, not job loss priority. "
        "Do not change the ML-predicted career risk level. "
        "Do not predict job loss. "
        "Do not say the user will definitely lose their job. "
        "Do not make final career decisions. "
        "Do not provide unrealistic guarantees. "
        "Do not invent user inputs. "
        "Keep the action plan practical, personalized, and time-bound. "
        "Use 30-day, 60-day, and 90-day career development steps. "
        "Base all recommendations only on the practical user inputs, model prediction, "
        "and system-derived indicators. "
        "recommendationMapping must be an array of objects with riskFactor, condition, "
        "lackingArea, and recommendation. "
        "mainRiskyAreas, careerStrengths, recommendedNextSteps, whyThisResult, "
        "thirtyDayPlan, sixtyDayPlan, ninetyDayPlan, prioritySkillsToImprove, "
        "suggestedLearningFocus, careerStrategyAdjustment, riskReductionActions, "
        "and progressTrackingSuggestions must be string arrays."
    )
    user_prompt = (
        "Write personalized Section 3 guidance as JSON, including an AI Career Resilience "
        "Action Plan with practical 30/60/90-day improvement steps. "
        f"For this role, prefer skill suggestions from: {role_hint}. "
        "Keep insights concise and professional. "
        "actionPriorityLevel should reflect decision-support urgency such as "
        "Low / Moderate / High Action Priority based on the predicted risk and indicators, "
        "without claiming job loss.\n\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        parsed = parse_openai_json(content)
        return normalize_guidance(parsed)
    except Exception as exc:
        return empty_guidance(
            f"AI guidance generation failed: {exc}. Model prediction and derived indicators are still available."
        )


def serialize_assessment_document(document):
    if not isinstance(document, dict):
        return document
    item = dict(document)
    raw_id = item.pop("_id", None)
    if isinstance(raw_id, ObjectId):
        item["id"] = str(raw_id)
    elif raw_id is not None:
        item["id"] = str(raw_id)

    created_at = item.get("createdAt")
    if isinstance(created_at, datetime):
        item["createdAt"] = created_at.isoformat()
    return item


def save_assessment_to_mongodb(practical_inputs, response_payload):
    """Best-effort MongoDB persistence. Never raises to callers."""
    if assessments_collection is None:
        print("MongoDB warning: collection unavailable; assessment was not saved.")
        return None

    record = {
        "practicalUserInputs": practical_inputs,
        "modelPrediction": response_payload.get("modelPrediction"),
        "systemDerivedIndicators": response_payload.get("systemDerivedIndicators"),
        "aiGeneratedGuidance": response_payload.get("aiGeneratedGuidance"),
        "decisionSupportNote": response_payload.get("decisionSupportNote"),
        "createdAt": datetime.now(timezone.utc),
    }

    try:
        result = assessments_collection.insert_one(record)
        return str(result.inserted_id)
    except Exception as mongo_save_error:  # noqa: BLE001
        print(f"MongoDB warning: failed to save assessment: {mongo_save_error}")
        return None


@app.get("/")
def home():
    if startup_error:
        return jsonify({"message": "API startup failed.", "error": startup_error}), 500
    return jsonify(
        {
            "message": "Career Safety and Industry Stability API is running.",
            "note": "Only overall career risk level is the main Random Forest prediction.",
        }
    ), 200


@app.post("/predict")
def predict():
    if startup_error or main_model is None:
        return jsonify(
            {
                "error": "Model or encoder artifacts failed to load.",
                "details": startup_error or "Model is unavailable.",
            }
        ), 500

    try:
        payload = request.get_json(silent=True)
        is_valid, error_message, clean_payload = validate_payload(payload)
        if not is_valid:
            return jsonify({"error": error_message}), 400

        scores = derive_scores(clean_payload)
        aux_levels = predict_auxiliary_levels(clean_payload, scores)

        automation_level = aux_levels.get("automation_exposure_level")
        domain_level = aux_levels.get("domain_stability_level")
        trend_level = aux_levels.get("job_market_trend_level")

        if automation_level not in AUTOMATION_TO_AI_REPLACEABILITY:
            raise ValueError(f"Unexpected automation_exposure_level: {automation_level}")
        if domain_level not in DOMAIN_TO_STABILITY:
            raise ValueError(f"Unexpected domain_stability_level: {domain_level}")
        if trend_level not in TREND_LEVEL_TO_MARKET:
            raise ValueError(f"Unexpected job_market_trend_level: {trend_level}")

        derived = {
            "automationExposure": automation_level,
            "industryDomainStability": domain_level,
            "jobMarketTrend": trend_level,
            "learningActivity": learning_activity_label(clean_payload["weekly_learning_time"]),
            "skillUpdateBehavior": skill_update_behavior_label(
                clean_payload["skill_update_frequency"]
            ),
            "roleSwitchingConfidence": scale_label(clean_payload["switch_confidence"]),
            "careerStrategyStatus": str(clean_payload["career_strategy"]).strip(),
            "stabilityIndicators": derive_stability_indicators(clean_payload),
            "aiReplaceability": AUTOMATION_TO_AI_REPLACEABILITY[automation_level],
            "domainStability": DOMAIN_TO_STABILITY[domain_level],
            "jobMarketTrendMapped": TREND_LEVEL_TO_MARKET[trend_level],
            "learningScore": scores["learning_score"],
            "skillUpdateScore": scores["skill_update_score"],
            "experienceScore": scores["experience_score"],
            "strategyScore": scores["strategy_score"],
            "adaptabilityScore": scores["adaptability_score"],
        }
        derived["jobMarketTrend"] = trend_level

        main_row = build_main_model_row(
            clean_payload,
            {
                "stabilityIndicators": derived["stabilityIndicators"],
                "aiReplaceability": derived["aiReplaceability"],
                "domainStability": derived["domainStability"],
                "jobMarketTrend": derived["jobMarketTrendMapped"],
            },
        )

        if not hasattr(main_model, "feature_names_in_"):
            return jsonify({"error": "Main model does not provide feature_names_in_."}), 500

        encoded_payload = encode_main_features(
            main_row, main_encoders, list(main_model.feature_names_in_)
        )
        input_df = pd.DataFrame([encoded_payload])[main_model.feature_names_in_]
        prediction = main_model.predict(input_df)[0]
        risk_level = decode_risk_label(prediction, main_encoders)

        model_prediction = {
            "predictedOutput": "Overall Career Risk Level",
            "value": risk_level,
            "note": MODEL_PREDICTION_NOTE,
        }
        ai_guidance = generate_ai_guidance(clean_payload, model_prediction, derived)

        response_payload = {
            "modelPrediction": model_prediction,
            "systemDerivedIndicators": derived,
            "aiGeneratedGuidance": ai_guidance,
            "decisionSupportNote": DECISION_SUPPORT_NOTE,
        }

        try:
            history_id = save_assessment(clean_payload, response_payload)
            response_payload["historyId"] = history_id
        except Exception as history_error:  # noqa: BLE001
            # History is best-effort; prediction should still return.
            response_payload["historyWarning"] = str(history_error)

        # Cloud persistence is best-effort and must not break /predict.
        mongo_id = save_assessment_to_mongodb(clean_payload, response_payload)
        if mongo_id:
            response_payload["mongoAssessmentId"] = mongo_id

        return jsonify(response_payload), 200
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as exc:
        return jsonify({"error": "Risk estimation failed.", "details": str(exc)}), 500


@app.get("/assessments")
def list_mongo_assessments():
    if assessments_collection is None:
        return jsonify(
            {
                "items": [],
                "warning": "MongoDB is not configured or unavailable.",
            }
        ), 200

    try:
        cursor = (
            assessments_collection.find()
            .sort("createdAt", DESCENDING)
            .limit(20)
        )
        items = [serialize_assessment_document(doc) for doc in cursor]
        return jsonify({"items": items}), 200
    except Exception as exc:
        print(f"MongoDB warning: failed to list assessments: {exc}")
        return jsonify(
            {
                "items": [],
                "warning": "Unable to load assessments from MongoDB.",
                "details": str(exc),
            }
        ), 200


@app.get("/history")
def history_list():
    try:
        limit = request.args.get("limit", default=50, type=int)
        limit = max(1, min(limit or 50, 100))
        return jsonify({"items": list_assessments(limit=limit)}), 200
    except Exception as exc:
        return jsonify({"error": "Unable to load history.", "details": str(exc)}), 500


@app.get("/history/<int:assessment_id>")
def history_detail(assessment_id: int):
    try:
        item = get_assessment(assessment_id)
        if item is None:
            return jsonify({"error": "Assessment not found."}), 404
        return jsonify(item), 200
    except Exception as exc:
        return jsonify({"error": "Unable to load assessment.", "details": str(exc)}), 500


@app.delete("/history/<int:assessment_id>")
def history_delete(assessment_id: int):
    try:
        deleted = delete_assessment(assessment_id)
        if not deleted:
            return jsonify({"error": "Assessment not found."}), 404
        return jsonify({"message": "Assessment deleted.", "id": assessment_id}), 200
    except Exception as exc:
        return jsonify({"error": "Unable to delete assessment.", "details": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
