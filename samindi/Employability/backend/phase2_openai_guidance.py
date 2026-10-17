"""Phase 02 evidence-grounded OpenAI recommendation layer.

Follows notebook 10 (Competence -> Employability):

1. frozen Linear Regression model predicts EVS_avg
2. construct scores, item scores, and SHAP become evidence
3. OpenAI converts that evidence into guidance
4. a rule-based fallback is used if the API fails

The language model does not calculate or change the employability score.
This module is Phase 02 only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from employability_impact import (
    impact_prompt_block,
    priority_area_name,
    priority_focus_sentence,
    priority_labels,
    trusted_learning_cards,
)

BACKEND_DIR = Path(__file__).resolve().parent
EMPLOYABILITY_DIR = BACKEND_DIR.parent
for env_file in [EMPLOYABILITY_DIR / ".env", BACKEND_DIR / ".env"]:
    if env_file.exists():
        load_dotenv(env_file, override=True)

FEATURES = ["LifeCareer_avg", "LearningInnovation_avg", "ITMedia_avg"]

AREA_DETAILS = {
    "LifeCareer_avg": {
        "label": "Life & Career Skills",
        "components": [
            "Adaptability",
            "Communication with diverse team members",
            "Project planning and execution",
            "Leadership ability",
        ],
        "career_relevance": (
            "Life & Career Skills support working effectively with others, "
            "adjusting to changing conditions, planning work, and taking on responsibility."
        ),
    },
    "LearningInnovation_avg": {
        "label": "Learning & Innovation Skills",
        "components": [
            "Reasoning and decision-making",
            "Communication and collaboration",
            "Creativity and innovation",
        ],
        "career_relevance": (
            "Learning & Innovation Skills support problem-solving, creative thinking, "
            "and effective collaboration in professional environments."
        ),
    },
    "ITMedia_avg": {
        "label": "IT & Media Skills",
        "components": [
            "Information access and evaluation",
            "Media communication skills",
            "Media analysis and creation",
        ],
        "career_relevance": (
            "IT & Media Skills support digital communication, information literacy, "
            "and producing media or content professionally."
        ),
    },
}

LEARNING_RESOURCES = {
    "LifeCareer_avg": [
        {
            "provider": "Open University OpenLearn",
            "resource_type": "Free course",
            "topic": "Working in groups and teams",
            "url": "https://www.open.edu/openlearn/money-business/leadership-management/working-groups-and-teams/content-section-0",
        },
        {
            "provider": "Google Career Certificates",
            "resource_type": "Official YouTube series",
            "topic": "Google Project Management Certificate lessons",
            "url": "https://www.youtube.com/playlist?list=PLTZYG7bZ1u6puLWxUtqAjZkIB4dB_JFzk",
        },
    ],
    "LearningInnovation_avg": [
        {
            "provider": "Imperial College London on Coursera",
            "resource_type": "Free-to-audit course",
            "topic": "Creative Thinking: Techniques and Tools for Success",
            "url": "https://www.coursera.org/learn/creative-thinking-techniques-and-tools-for-success",
        },
        {
            "provider": "Open University OpenLearn",
            "resource_type": "Free course",
            "topic": "Extending and developing your thinking skills",
            "url": "https://www.open.edu/openlearn/education-development/extending-and-developing-your-thinking-skills/content-section-0",
        },
    ],
    "ITMedia_avg": [
        {
            "provider": "Open University OpenLearn with Microsoft",
            "resource_type": "Free course",
            "topic": "Digital skills: succeeding in a digital world",
            "url": "https://www.open.edu/openlearn/openlearn/digital-computing/digital-skills-succeeding-digital-world",
        },
        {
            "provider": "Crash Course with Stanford History Education Group and the Poynter Institute",
            "resource_type": "Official YouTube series",
            "topic": "Navigating Digital Information",
            "url": "https://www.youtube.com/watch?v=pLlv2o6UfTU",
        },
    ],
}

RULE_BASED_RECOMMENDATIONS = {
    "LifeCareer_avg": [
        "Take responsibility for planning a small academic or team project.",
        "Practice giving short presentations and leading group discussions.",
        "Use a weekly planning system to improve organization and adaptability.",
    ],
    "LearningInnovation_avg": [
        "Practice solving one structured case study each week.",
        "Participate in group brainstorming or innovation activities.",
        "Use decision-making frameworks to compare alternative solutions.",
    ],
    "ITMedia_avg": [
        "Practice evaluating the reliability of online information sources.",
        "Create professional presentations or digital content for academic projects.",
        "Improve digital communication through structured email, reports, and presentations.",
    ],
}

RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "area_analysis": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "area": {"type": "string"},
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "areas_for_improvement": {"type": "array", "items": {"type": "string"}},
                    "career_readiness_impact": {"type": "string"},
                    "practical_suggestions": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "area",
                    "strengths",
                    "areas_for_improvement",
                    "career_readiness_impact",
                    "practical_suggestions",
                ],
                "additionalProperties": False,
            },
        },
        "top_3_strengths": {"type": "array", "items": {"type": "string"}},
        "top_3_areas_for_improvement": {"type": "array", "items": {"type": "string"}},
        "personalized_action_plan": {"type": "array", "items": {"type": "string"}},
        "overall_career_readiness_summary": {"type": "string"},
        "recommended_next_steps": {"type": "array", "items": {"type": "string"}},
        "recommended_learning_resources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "area": {"type": "string"},
                    "provider": {"type": "string"},
                    "resource_type": {"type": "string"},
                    "topic": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["area", "provider", "resource_type", "topic", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "area_analysis",
        "top_3_strengths",
        "top_3_areas_for_improvement",
        "personalized_action_plan",
        "overall_career_readiness_summary",
        "recommended_next_steps",
        "recommended_learning_resources",
    ],
    "additionalProperties": False,
}

_EXPLAINER_CACHE: Dict[str, Any] = {"ready": False, "explainer": None, "scaler": None, "linear": None}


def _level(score: float) -> str:
    if score >= 4:
        return "Strong"
    if score >= 3:
        return "Developing"
    return "Needs Improvement"


def _shap_effect(value: float) -> str:
    if abs(value) < 1e-6:
        return "Little or no measured influence on this prediction"
    if value > 0:
        return "Increased the predicted employability score"
    return "Decreased the predicted employability score"


def _linear_contributions(model, frame: pd.DataFrame) -> Dict[str, float]:
    scaler = model.named_steps.get("scaler")
    linear = model.named_steps.get("model")
    if scaler is None or linear is None or not hasattr(linear, "coef_"):
        return {name: 0.0 for name in frame.columns}
    scaled = np.asarray(scaler.transform(frame), dtype=float)[0]
    return {name: float(linear.coef_[index] * scaled[index]) for index, name in enumerate(frame.columns)}


def explain_constructs(model, constructs: Dict[str, float], feature_names: List[str]) -> Dict[str, float]:
    frame = pd.DataFrame([[constructs[name] for name in feature_names]], columns=feature_names)
    try:
        import shap

        scaler = model.named_steps.get("scaler")
        linear = model.named_steps.get("model")
        if scaler is None or linear is None:
            return _linear_contributions(model, frame)

        if not _EXPLAINER_CACHE["ready"]:
            background_path = BACKEND_DIR / "data" / "processed" / "phase2_competence_prepared.csv"
            if background_path.exists():
                prepared = pd.read_csv(background_path)
                background = prepared[feature_names].sample(
                    n=min(100, len(prepared)),
                    random_state=42,
                )
                scaled_background = pd.DataFrame(scaler.transform(background), columns=feature_names)
                _EXPLAINER_CACHE["explainer"] = shap.LinearExplainer(linear, scaled_background)
            _EXPLAINER_CACHE["scaler"] = scaler
            _EXPLAINER_CACHE["linear"] = linear
            _EXPLAINER_CACHE["ready"] = True

        explainer = _EXPLAINER_CACHE.get("explainer")
        if explainer is not None:
            scaled_input = pd.DataFrame(scaler.transform(frame), columns=feature_names)
            values = explainer(scaled_input).values[0]
            return {name: float(values[index]) for index, name in enumerate(feature_names)}
    except Exception:
        pass
    return _linear_contributions(model, frame)


def build_evidence(
    constructs: Dict[str, float],
    item_analysis: List[Dict[str, Any]],
    shap_values: Dict[str, float],
    prediction: float,
    construct_items: Dict[str, List[str]],
    construct_labels: Dict[str, str],
) -> Dict[str, Any]:
    feature_rows = []
    for feature in FEATURES:
        details = AREA_DETAILS[feature]
        score = float(constructs[feature])
        shap_value = float(shap_values.get(feature, 0.0))
        feature_rows.append(
            {
                "feature": feature,
                "label": construct_labels[feature],
                "score": score,
                "level": _level(score),
                "shap_value": shap_value,
                "effect": _shap_effect(shap_value),
                "career_relevance": details["career_relevance"],
                "components": details["components"],
                "items": construct_items[feature],
            }
        )
    return {
        "predicted_evs_avg": float(prediction),
        "feature_evidence": feature_rows,
        "item_evidence": item_analysis,
        "strongest_feature": max(feature_rows, key=lambda row: row["score"]),
        "weakest_feature": min(feature_rows, key=lambda row: row["score"]),
    }


def select_learning_resources(evidence: Dict[str, Any], max_resources_per_area: int = 2) -> List[Dict[str, str]]:
    selected = []
    for row in sorted(evidence["feature_evidence"], key=lambda item: item["score"]):
        if row["score"] >= 4.0:
            continue
        for resource in LEARNING_RESOURCES[row["feature"]][:max_resources_per_area]:
            selected.append(
                {
                    "area": row["label"],
                    "provider": resource["provider"],
                    "resource_type": resource["resource_type"],
                    "topic": resource["topic"],
                    "url": resource["url"],
                }
            )
    return selected


def generate_rule_based_recommendation(evidence: Dict[str, Any]) -> Dict[str, Any]:
    area_analysis = []
    items = evidence["item_evidence"]
    item_by_code = {item["code"]: item for item in items}

    for row in evidence["feature_evidence"]:
        area_items = [item_by_code[code] for code in row["items"] if code in item_by_code]
        strengths = [f"{item['name']} ({item['score']:.1f}/5)" for item in area_items if item["score"] >= 4]
        improvements = [f"{item['name']} ({item['score']:.1f}/5)" for item in area_items if item["score"] < 4]
        if not strengths:
            strengths = ["This competence area is still developing."]
        if not improvements:
            improvements = ["Maintain current performance and continue advanced development."]
        area_analysis.append(
            {
                "area": row["label"],
                "strengths": strengths[:3],
                "areas_for_improvement": improvements[:3],
                "career_readiness_impact": (
                    f"{row['career_relevance']} The model-level SHAP contribution was "
                    f"{row['shap_value']:.4f}, indicating it {row['effect'].lower()}."
                ),
                "practical_suggestions": RULE_BASED_RECOMMENDATIONS[row["feature"]][:3],
            }
        )

    top_strengths = sorted(items, key=lambda item: item["score"], reverse=True)[:3]
    ranking = evidence.get("impact_ranking") or []
    impact_labels = priority_labels(ranking)
    top_improvements = sorted(items, key=lambda item: item["score"])[:3]
    selected_resources = select_learning_resources(evidence)
    priority_name = priority_area_name(ranking, evidence["weakest_feature"]["label"])
    return {
        "area_analysis": area_analysis,
        "top_3_strengths": [f"{item['name']} ({item['score']:.1f}/5)" for item in top_strengths],
        "top_3_areas_for_improvement": impact_labels
        or [f"{item['name']} ({item['score']:.1f}/5)" for item in top_improvements],
        "personalized_action_plan": [
            priority_focus_sentence(ranking, "Focus first on the three lowest-scoring competence items."),
            "Complete practical activities related to the priority competence area.",
            "Review progress after four weeks and repeat the competence assessment.",
        ],
        "overall_career_readiness_summary": (
            f"The predicted employability score is {evidence['predicted_evs_avg']:.2f} / 5. "
            f"The strongest competence construct is {evidence['strongest_feature']['label']}, "
            f"while {priority_name} is the priority development area."
        ),
        "recommended_next_steps": [
            "Choose one priority competence area for immediate development.",
            "Complete at least one practical learning activity or project.",
            "Track improvement and reassess after one month.",
        ],
        "recommended_learning_resources": [
            {
                "area": resource["area"],
                "provider": resource["provider"],
                "resource_type": resource["resource_type"],
                "topic": resource["topic"],
                "reason": f"Recommended to support development in {resource['area']}.",
            }
            for resource in selected_resources
        ],
        "source": "rule_based_fallback",
    }


def build_api_prompt(evidence: Dict[str, Any], selected_resources: List[Dict[str, str]]) -> str:
    area_blocks = []
    for row in evidence["feature_evidence"]:
        area_blocks.append(
            f"""
Area: {row['label']}
Construct Score: {row['score']:.2f}/5
Interpretation: {row['level']}
SHAP contribution: {row['shap_value']:.4f}
Model effect: {row['effect']}
Components: {', '.join(row['components'])}
Career relevance: {row['career_relevance']}
"""
        )

    item_lines = [
        f"- {item.get('construct', '')} | {item['name']}: {item['score']:.1f}/5 ({item['level']})"
        for item in evidence["item_evidence"]
    ]

    return f"""
Analyze the competence evidence below and generate a personalized
career-development recommendation.

The Employability prediction has already been generated by a trained
machine learning model.

Predicted Employability Score:
{evidence['predicted_evs_avg']:.3f} / 5

Construct-Level Model Evidence:
{''.join(area_blocks)}

Individual Survey Evidence:
{chr(10).join(item_lines)}

Strongest observed competence construct:
{evidence['strongest_feature']['label']}

Lowest observed competence construct:
{evidence['weakest_feature']['label']}

{impact_prompt_block(evidence.get('impact_ranking') or [])}

Approved Learning Resources:
{json.dumps(selected_resources, indent=2)}

For each competence area:

1. Identify specific strengths using the individual survey item scores.
2. Identify specific areas that may benefit from further development.
3. Explain briefly why the competence area is relevant to career readiness.
4. Provide 2-3 practical and realistic improvement suggestions.

Then provide:

- Top 3 Strengths
- Top 3 Areas for Improvement
- Personalized Action Plan
- Overall Career Readiness Summary
- Recommended Next Steps
- Recommended Learning Resources

Important rules:

- Do not calculate or modify the Employability prediction.
- Use construct-level SHAP evidence only to explain model behaviour.
- Use individual survey item scores to identify specific strengths and weaknesses.
- Do not infer a specific skill strength or weakness from a construct average alone.
- Use only the supplied evidence.
- Use learning resources only from the Approved Learning Resources list.
- Do not invent URLs, qualifications, experience, or personal facts.
- Do not make causal claims.
- Do not make medical or psychological diagnoses.
- Do not assume information not contained in the evidence.
- Keep recommendations supportive, practical, and specific.
- Do not state or imply that improving a competence will necessarily increase Employability.
- When discussing SHAP, describe only how the feature influenced the model prediction.
- Recommendations should be framed as career-development opportunities, not guaranteed methods for increasing the predicted score.
"""


def _parse_json_text(raw_text: str) -> Dict[str, Any]:
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def generate_api_recommendation(evidence: Dict[str, Any], selected_resources: List[Dict[str, str]]) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "your_openai_api_key_here":
        raise RuntimeError("OPENAI_API_KEY is missing in samindi/Employability/.env")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model_name = (os.getenv("OPENAI_GUIDANCE_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
    prompt = build_api_prompt(evidence, selected_resources)
    system_message = "You generate evidence-grounded career-development guidance."

    try:
        response = client.responses.create(
            model=model_name,
            input=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "career_recommendation",
                    "strict": True,
                    "schema": RECOMMENDATION_SCHEMA,
                }
            },
        )
        result = _parse_json_text(response.output_text)
    except Exception:
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_message + " Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        result = _parse_json_text(response.choices[0].message.content)

    result["source"] = "openai_api"
    return result


def generate_recommendation(evidence: Dict[str, Any]) -> Dict[str, Any]:
    selected_resources = select_learning_resources(evidence)
    try:
        result = generate_api_recommendation(evidence, selected_resources)
    except Exception:
        result = generate_rule_based_recommendation(evidence)
    result["recommended_learning_resources"] = trusted_learning_cards(selected_resources)
    return result


def attach_phase2_recommendations(
    payload: Dict[str, Any],
    model,
    constructs: Dict[str, float],
    item_analysis: List[Dict[str, Any]],
    construct_analysis: List[Dict[str, Any]],
    prediction: float,
    item_labels: Dict[str, str],
    construct_items: Dict[str, List[str]],
    construct_labels: Dict[str, str],
    action_library: Dict[str, str],
) -> Dict[str, Any]:
    shap_values = explain_constructs(model, constructs, FEATURES)
    reverse_construct = {
        item_code: construct_labels[feature]
        for feature, codes in construct_items.items()
        for item_code in codes
    }
    labeled_items = []
    for item in item_analysis:
        labeled = dict(item)
        labeled["construct"] = reverse_construct.get(item["code"], "")
        labeled_items.append(labeled)

    evidence = build_evidence(
        constructs=constructs,
        item_analysis=labeled_items,
        shap_values=shap_values,
        prediction=prediction,
        construct_items=construct_items,
        construct_labels=construct_labels,
    )
    evidence["impact_ranking"] = payload.get("impact_ranking") or []
    recommendation = generate_recommendation(evidence)

    code_to_action = {}
    for area in recommendation.get("area_analysis", []):
        suggestions = area.get("practical_suggestions") or []
        if not suggestions:
            continue
        for feature, label in construct_labels.items():
            if area.get("area") == label:
                for item_code in construct_items[feature]:
                    code_to_action[item_code] = suggestions[0]

    improved_areas = []
    for area in payload.get("areas_for_improvement", []):
        updated = dict(area)
        code = updated.get("focus_item_code") or updated.get("code")
        if code in code_to_action:
            updated["action"] = code_to_action[code]
        elif code in action_library:
            updated["action"] = action_library[code]
        improved_areas.append(updated)

    payload["areas_for_improvement"] = improved_areas
    payload["ai_recommendation"] = recommendation
    payload["recommendation_source"] = recommendation.get("source", "rule_based_fallback")
    payload["shap_explanation"] = {key: round(value, 6) for key, value in shap_values.items()}
    payload["note"] = (
        "The employability score is produced only by the frozen Linear Regression model. "
        "OpenAI is used only to turn model evidence into personalized guidance."
    )
    _ = item_labels
    _ = construct_analysis
    return payload
