import re
import pandas as pd
import joblib

# ==========================================================
# MODEL PATH
# ==========================================================
MODEL_FILE = "../models/best_communication_skill_model.pkl"

model = joblib.load(MODEL_FILE)


# ==========================================================
# TEXT CLEANING
# ==========================================================
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ==========================================================
# COMMUNICATION SCORE CALCULATION
# ==========================================================
def calculate_scores(text):
    text = clean_text(text)
    words = text.split()
    word_count = len(words)

    # Clarity score
    if word_count < 20:
        clarity_score = 30
    elif word_count < 50:
        clarity_score = 55
    elif word_count < 100:
        clarity_score = 75
    else:
        clarity_score = 90

    # Structure score
    structure_keywords = [
        "first", "second", "then", "finally", "because",
        "for example", "therefore", "in conclusion",
        "my role", "i worked", "i developed", "i created"
    ]

    structure_count = sum(1 for keyword in structure_keywords if keyword in text)

    if structure_count == 0:
        structure_score = 30
    elif structure_count <= 2:
        structure_score = 60
    elif structure_count <= 4:
        structure_score = 80
    else:
        structure_score = 95

    # Professional expression score
    professional_keywords = [
        "experience", "skills", "project", "team", "responsibility",
        "developed", "implemented", "designed", "improved",
        "software", "database", "frontend", "backend", "ai",
        "machine learning", "communication", "problem solving",
        "leadership", "collaboration", "technical", "analysis",
        "quality", "testing", "requirements", "solution"
    ]

    professional_count = sum(1 for keyword in professional_keywords if keyword in text)

    if professional_count == 0:
        professional_score = 25
    elif professional_count <= 2:
        professional_score = 55
    elif professional_count <= 5:
        professional_score = 75
    else:
        professional_score = 90

    # Weak words penalty
    weak_words = [
        "i don't know", "not sure", "maybe", "something",
        "like", "um", "uh", "actually"
    ]

    weak_count = sum(text.count(word) for word in weak_words)
    penalty = min(20, weak_count * 3)

    final_score = int(
        (clarity_score * 0.35) +
        (structure_score * 0.30) +
        (professional_score * 0.35) -
        penalty
    )

    final_score = max(0, min(100, final_score))

    return clarity_score, structure_score, professional_score, final_score


# ==========================================================
# LABEL DISPLAY FORMAT
# ==========================================================
def format_skill_level(label):
    label = str(label).lower()

    if label == "poor":
        return "Poor Communication"
    elif label == "average":
        return "Average Communication"
    elif label == "good":
        return "Good Communication"
    elif label == "excellent":
        return "Excellent Communication"
    else:
        return "Unknown Communication Level"


# ==========================================================
# FEEDBACK AND SUGGESTIONS
# ==========================================================
def get_feedback_and_suggestions(label):
    label = str(label).lower()

    if label == "poor":
        feedback = (
            "Your communication needs improvement. The answer should be clearer, "
            "more complete, and better structured."
        )
        suggestions = [
            "Start with a clear self-introduction.",
            "Explain your skills and project properly.",
            "Reduce pauses and filler words.",
            "Improve grammar and sentence flow."
        ]

    elif label == "average":
        feedback = (
            "Your communication is understandable, but it needs better structure, "
            "more detail, and stronger professional wording."
        )
        suggestions = [
            "Use the STAR method: Situation, Task, Action, Result.",
            "Add more details about your project role.",
            "Use professional words related to skills and experience.",
            "Make the answer more confident and organized."
        ]

    elif label == "good":
        feedback = (
            "Your communication is good. You explain your ideas clearly, but you can "
            "improve by adding stronger examples and a more confident ending."
        )
        suggestions = [
            "Add measurable project results if possible.",
            "Connect your skills more clearly with the job role.",
            "Use a strong closing sentence.",
            "Maintain a confident and professional tone."
        ]

    elif label == "excellent":
        feedback = (
            "Your communication is excellent. The answer is clear, structured, "
            "professional, and suitable for interview readiness."
        )
        suggestions = [
            "Maintain the same clear structure.",
            "Continue using professional examples.",
            "Keep answers focused on the selected job role.",
            "Use this style for future interview practice."
        ]

    else:
        feedback = "Unable to generate feedback for the predicted communication level."
        suggestions = [
            "Check the transcript quality.",
            "Try again with a clearer audio response."
        ]

    return feedback, suggestions


# ==========================================================
# PREDICTION FUNCTION
# ==========================================================
def predict_communication(answer):
    cleaned_answer = clean_text(answer)

    clarity, structure, professional, final_score = calculate_scores(answer)

    input_data = pd.DataFrame([{
        "clean_transcript": cleaned_answer,
        "clarity_score": clarity,
        "structure_score": structure,
        "professional_expression_score": professional,
        "final_score": final_score
    }])

    prediction = model.predict(input_data)[0]

    confidence = 0
    if hasattr(model.named_steps["classifier"], "predict_proba"):
        confidence = max(model.predict_proba(input_data)[0]) * 100

    skill_level = format_skill_level(prediction)
    feedback, suggestions = get_feedback_and_suggestions(prediction)

    return {
        "skill_level": skill_level,
        "confidence": confidence,
        "feedback": feedback,
        "suggestions": suggestions,
        "clarity_score": clarity,
        "structure_score": structure,
        "professional_expression_score": professional,
        "final_score": final_score
    }


# ==========================================================
# TEST SAMPLE ANSWER
# Change this answer to test different outputs
# ==========================================================
sample_answer = """
I don't know properly. My name is Kasuni. I did some project. 
It is about software. I know little Python and Java. 
I want job because I like IT. Sometimes I forget what to say.
"""

result = predict_communication(sample_answer)

print("Skill Level:", result["skill_level"])
print("Confidence:", round(result["confidence"], 2), "%")
print("Feedback:", result["feedback"])
print("Suggestions:", result["suggestions"])

print("\n--- Score Details ---")
print("Clarity Score:", result["clarity_score"])
print("Structure Score:", result["structure_score"])
print("Professional Expression Score:", result["professional_expression_score"])
print("Final Score:", result["final_score"])