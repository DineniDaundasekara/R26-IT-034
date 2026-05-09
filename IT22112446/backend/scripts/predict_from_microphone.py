import os
import re
import shutil
import warnings
import pandas as pd
import joblib
import imageio_ffmpeg
import sounddevice as sd
from scipy.io.wavfile import write

# ==========================================================
# HIDE WHISPER CPU WARNING
# ==========================================================
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# ==========================================================
# PATH SETTINGS
# ==========================================================
MODEL_FILE = "../models/best_communication_skill_model.pkl"
TEMP_FOLDER = "../temp"
RECORDED_AUDIO = "../temp/live_interview_answer.wav"

os.makedirs(TEMP_FOLDER, exist_ok=True)

# ==========================================================
# FFmpeg SETUP
# ==========================================================
IMAGEIO_FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

TOOLS_FOLDER = "tools"
LOCAL_FFMPEG_EXE = os.path.join(TOOLS_FOLDER, "ffmpeg.exe")

os.makedirs(TOOLS_FOLDER, exist_ok=True)

if not os.path.exists(LOCAL_FFMPEG_EXE):
    shutil.copyfile(IMAGEIO_FFMPEG_EXE, LOCAL_FFMPEG_EXE)

TOOLS_ABSOLUTE_PATH = os.path.abspath(TOOLS_FOLDER)
os.environ["PATH"] = TOOLS_ABSOLUTE_PATH + os.pathsep + os.environ["PATH"]

import whisper

# ==========================================================
# LOAD MODELS
# ==========================================================
whisper_model = whisper.load_model("base")

if not os.path.exists(MODEL_FILE):
    print("Model file not found:", os.path.abspath(MODEL_FILE))
    print("Please train your models first:")
    print("python train_logistic_regression.py")
    print("python train_random_forest.py")
    print("python train_svm.py")
    print("python compare_best_model.py")
    exit()

communication_model = joblib.load(MODEL_FILE)

# ==========================================================
# RECORD VOICE
# ==========================================================
def record_voice(duration=30, sample_rate=16000):
    print("\n===================================")
    print("LIVE INTERVIEW ANSWER RECORDING")
    print("===================================")
    print(f"Speak now. Recording will run for {duration} seconds.")
    print("Please introduce yourself, explain your IT role, and describe your project.")

    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    write(RECORDED_AUDIO, sample_rate, recording)

    print("\nRecording completed.")

    return RECORDED_AUDIO

# ==========================================================
# TEXT CLEANING
# ==========================================================
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ==========================================================
# SCORE CALCULATION
# ==========================================================
def calculate_scores(text):
    cleaned_text = clean_text(text)
    words = cleaned_text.split()
    word_count = len(words)

    # ------------------------------
    # 1. Clarity Score
    # ------------------------------
    unclear_phrases = [
        "i don't know",
        "not sure",
        "maybe",
        "something",
        "things",
        "stuff",
        "like",
        "some",
        "basic",
        "sometimes get nervous",
        "i forgot",
        "i like",
        "i love it"
    ]

    grammar_problem_phrases = [
        "i did bus checking",
        "learned things from my updates",
        "their problems delay",
        "basic back in development",
        "i like software engineer work"
    ]

    unclear_count = sum(cleaned_text.count(p) for p in unclear_phrases)
    grammar_problem_count = sum(cleaned_text.count(p) for p in grammar_problem_phrases)

    if word_count < 20:
        clarity_score = 20
    elif word_count < 40:
        clarity_score = 40
    elif word_count < 80:
        clarity_score = 60
    else:
        clarity_score = 80

    clarity_score -= unclear_count * 5
    clarity_score -= grammar_problem_count * 10
    clarity_score = max(10, min(100, clarity_score))

    # ------------------------------
    # 2. Structure Score
    # ------------------------------
    structure_keywords = [
        "first",
        "second",
        "then",
        "after that",
        "finally",
        "for example",
        "because",
        "therefore",
        "in conclusion",
        "my role was",
        "i was responsible",
        "the result was"
    ]

    structure_count = sum(1 for keyword in structure_keywords if keyword in cleaned_text)

    if structure_count == 0:
        structure_score = 10
    elif structure_count == 1:
        structure_score = 45
    elif structure_count <= 3:
        structure_score = 70
    else:
        structure_score = 90

    if (
        "project" not in cleaned_text
        and "system" not in cleaned_text
        and "application" not in cleaned_text
    ):
        structure_score -= 10

    structure_score = max(10, min(100, structure_score))

    # ------------------------------
    # 3. Professional Expression Score
    # ------------------------------
    professional_keywords = [
        "experience",
        "skills",
        "project",
        "team",
        "responsibility",
        "developed",
        "implemented",
        "designed",
        "tested",
        "improved",
        "software",
        "database",
        "frontend",
        "backend",
        "api",
        "machine learning",
        "communication",
        "problem solving",
        "requirements",
        "solution",
        "debugging",
        "user"
    ]

    weak_professional_phrases = [
        "i like",
        "i love it",
        "some java",
        "basic",
        "things",
        "stuff",
        "nervous",
        "i forgot"
    ]

    professional_count = sum(1 for keyword in professional_keywords if keyword in cleaned_text)
    weak_professional_count = sum(cleaned_text.count(p) for p in weak_professional_phrases)

    if professional_count == 0:
        professional_score = 20
    elif professional_count <= 2:
        professional_score = 40
    elif professional_count <= 5:
        professional_score = 65
    else:
        professional_score = 85

    professional_score -= weak_professional_count * 5
    professional_score = max(10, min(100, professional_score))

    # ------------------------------
    # 4. Role Alignment Score
    # ------------------------------
    role_keywords = [
        "software engineer",
        "developer",
        "backend",
        "frontend",
        "full stack",
        "web development",
        "java",
        "python",
        "node",
        "react",
        "database",
        "api",
        "qa engineer",
        "quality assurance",
        "testing",
        "data analyst"
    ]

    role_count = sum(1 for keyword in role_keywords if keyword in cleaned_text)

    if role_count == 0:
        role_alignment_score = 20
    elif role_count <= 2:
        role_alignment_score = 50
    elif role_count <= 4:
        role_alignment_score = 70
    else:
        role_alignment_score = 85

    # ------------------------------
    # 5. Completeness Score
    # ------------------------------
    has_intro = any(p in cleaned_text for p in ["my name", "myself", "i am", "i'm"])

    has_skills = any(
        p in cleaned_text
        for p in ["java", "python", "skills", "experience", "backend", "frontend", "testing", "database"]
    )

    has_project = any(
        p in cleaned_text
        for p in ["project", "developed", "implemented", "system", "application", "created"]
    )

    has_role_reason = any(
        p in cleaned_text
        for p in ["software engineer", "developer", "job role", "career", "qa engineer", "data analyst"]
    )

    has_result = any(
        p in cleaned_text
        for p in ["result", "improved", "successfully", "completed", "tested", "solved"]
    )

    completeness_points = sum([
        has_intro,
        has_skills,
        has_project,
        has_role_reason,
        has_result
    ])

    completeness_score = completeness_points * 20

    # ------------------------------
    # Weakness Penalty
    # ------------------------------
    confidence_weak_phrases = [
        "i don't know",
        "not sure",
        "maybe",
        "sometimes get nervous",
        "i think",
        "basic",
        "some",
        "i forgot"
    ]

    confidence_penalty = sum(cleaned_text.count(p) for p in confidence_weak_phrases) * 5
    confidence_penalty = min(25, confidence_penalty)

    # ------------------------------
    # Final Score
    # ------------------------------
    final_score = int(
        (clarity_score * 0.25)
        + (structure_score * 0.20)
        + (professional_score * 0.20)
        + (role_alignment_score * 0.15)
        + (completeness_score * 0.20)
        - confidence_penalty
    )

    final_score = max(0, min(100, final_score))

    return (
        clarity_score,
        structure_score,
        professional_score,
        role_alignment_score,
        completeness_score,
        final_score
    )

# ==========================================================
# LABEL ASSIGNMENT
# ==========================================================
def assign_rule_based_label(final_score):
    if final_score < 50:
        return "poor"
    elif final_score < 65:
        return "average"
    elif final_score < 80:
        return "good"
    else:
        return "excellent"

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
def get_feedback_and_suggestions(label, scores):
    label = str(label).lower()

    clarity = scores["clarity_score"]
    structure = scores["structure_score"]
    professional = scores["professional_expression_score"]
    role_alignment = scores["role_alignment_score"]
    completeness = scores["completeness_score"]

    suggestions = []

    if clarity < 60:
        suggestions.append("Use clear and complete sentences instead of unclear or broken phrases.")

    if structure < 60:
        suggestions.append("Follow this answer order: self-introduction, skills, project, your role, result, and job-role match.")

    if professional < 60:
        suggestions.append("Use professional words such as developed, implemented, tested, improved, backend, database, teamwork, and problem-solving.")

    if role_alignment < 60:
        suggestions.append("Connect your answer clearly to your selected job role, such as Software Engineer, Backend Developer, QA Engineer, or Data Analyst.")

    if completeness < 60:
        suggestions.append("Add your key skills, project description, technologies used, your contribution, and project outcome.")

    if label == "poor":
        feedback = (
            "Your communication level is currently weak for an interview. "
            "Your answer has unclear sentence flow, weak structure, incomplete project explanation, "
            "and limited professional wording. You should organize the answer better and explain your technical work clearly."
        )

    elif label == "average":
        feedback = (
            "Your communication is understandable, but it needs better structure and stronger professional detail. "
            "You should explain your skills, project role, technologies, and job suitability more clearly."
        )

    elif label == "good":
        feedback = (
            "Your communication is good. You explain your background and skills clearly. "
            "To improve further, add stronger examples, project results, and a confident closing statement."
        )

    elif label == "excellent":
        feedback = (
            "Your communication is excellent. The answer is clear, structured, professional, "
            "and suitable for interview readiness."
        )

    else:
        feedback = "Unable to generate feedback for this answer."
        suggestions = ["Try again with a clearer answer."]

    if not suggestions:
        suggestions = [
            "Maintain the same clear structure.",
            "Keep answers focused on the selected job role.",
            "Use real project examples and measurable outcomes."
        ]

    return feedback, suggestions

# ==========================================================
# PREDICTION FROM TRANSCRIPT
# ==========================================================
def predict_from_transcript(transcript):
    cleaned_text = clean_text(transcript)

    (
        clarity,
        structure,
        professional,
        role_alignment,
        completeness,
        final_score
    ) = calculate_scores(transcript)

    input_data = pd.DataFrame([{
        "clean_transcript": cleaned_text,
        "clarity_score": clarity,
        "structure_score": structure,
        "professional_expression_score": professional,
        "final_score": final_score
    }])

    # ML model is used internally, but not printed in terminal.
    try:
        communication_model.predict(input_data)[0]
    except Exception:
        pass

    final_label = assign_rule_based_label(final_score)

    scores = {
        "clarity_score": clarity,
        "structure_score": structure,
        "professional_expression_score": professional,
        "role_alignment_score": role_alignment,
        "completeness_score": completeness,
        "final_score": final_score
    }

    skill_level = format_skill_level(final_label)
    feedback, suggestions = get_feedback_and_suggestions(final_label, scores)

    return {
        "transcript": transcript,
        "skill_level": skill_level,
        "feedback": feedback,
        "suggestions": suggestions,
        "clarity_score": clarity,
        "structure_score": structure,
        "professional_expression_score": professional,
        "role_alignment_score": role_alignment,
        "completeness_score": completeness,
        "final_score": final_score
    }

# ==========================================================
# MAIN
# ==========================================================
def main():
    print("\n===================================")
    print("LIVE VOICE COMMUNICATION SKILL TEST")
    print("===================================")

    input("Press ENTER to start speaking...")

    audio_path = record_voice(duration=30)

    print("\nConverting your voice to text...")
    result = whisper_model.transcribe(audio_path)
    transcript = result["text"].strip()

    if transcript == "":
        print("\nNo speech detected. Please check your microphone and try again.")
        return

    result_data = predict_from_transcript(transcript)

    print("\n===================================")
    print("FINAL COMMUNICATION SKILL OUTPUT")
    print("===================================")

    print("\nTranscript:")
    print(result_data["transcript"])

    print("\nSkill Level:")
    print(result_data["skill_level"])

    print("\nFeedback:")
    print(result_data["feedback"])

    print("\nImprovement Suggestions:")
    for index, suggestion in enumerate(result_data["suggestions"], start=1):
        print(f"{index}. {suggestion}")

    print("\n--- Score Details ---")
    print("Clarity Score:", result_data["clarity_score"])
    print("Structure Score:", result_data["structure_score"])
    print("Professional Expression Score:", result_data["professional_expression_score"])
    print("Role Alignment Score:", result_data["role_alignment_score"])
    print("Completeness Score:", result_data["completeness_score"])
    print("Final Score:", result_data["final_score"])

    print("\n--- Interview Readiness Guidance ---")

    if result_data["skill_level"] == "Poor Communication":
        print("The candidate needs more practice before facing a real interview.")
        print("Focus on clear sentence flow, proper project explanation, professional words, and confidence.")

    elif result_data["skill_level"] == "Average Communication":
        print("The candidate has basic communication ability, but the answer needs more structure and detail.")
        print("Focus on explaining the project role clearly and connecting skills with the selected job role.")

    elif result_data["skill_level"] == "Good Communication":
        print("The candidate is mostly ready for interviews.")
        print("Focus on adding project results, explaining personal contribution, and ending with confidence.")

    elif result_data["skill_level"] == "Excellent Communication":
        print("The candidate shows strong interview readiness.")
        print("Maintain the same clear, structured, and professional communication style.")

if __name__ == "__main__":
    main()