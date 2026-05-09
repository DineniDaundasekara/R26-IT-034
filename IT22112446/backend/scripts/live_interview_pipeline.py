import os
import re
import json
import shutil
import warnings
from datetime import datetime

import pandas as pd
import joblib
import imageio_ffmpeg
import sounddevice as sd
from scipy.io.wavfile import write
from dotenv import load_dotenv
from groq import Groq

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# ==========================================================
# PATH SETTINGS
# ==========================================================
MODEL_FILE = "../models/best_communication_skill_model.pkl"
TEMP_FOLDER = "../temp"
OUTPUT_FOLDER = "../outputs"
ENV_FILE = "../.env"

RECORDED_AUDIO_FILE = "../temp/live_interview_answer.wav"

os.makedirs(TEMP_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ==========================================================
# LOAD GROQ API KEY
# ==========================================================
load_dotenv(ENV_FILE)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("GROQ_API_KEY not found.")
    print("Please create backend/.env and add:")
    print("GROQ_API_KEY=your_groq_api_key_here")
    exit()

groq_client = Groq(api_key=GROQ_API_KEY)

# ==========================================================
# FFMPEG SETUP FOR WHISPER
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
print("Loading Whisper model...")
whisper_model = whisper.load_model("base")

print("Loading best communication skill model...")

if not os.path.exists(MODEL_FILE):
    print("Best model not found:", os.path.abspath(MODEL_FILE))
    print("Please run compare_best_model.py first.")
    exit()

communication_model = joblib.load(MODEL_FILE)


# ==========================================================
# RECORD LIVE AUDIO
# ==========================================================
def record_live_audio(duration=30, sample_rate=16000):
    print("\n===================================")
    print("LIVE INTERVIEW RECORDING")
    print("===================================")
    print(f"Recording will run for {duration} seconds.")
    print("Speak now: introduce yourself, explain your role, skills, and project.")

    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    write(RECORDED_AUDIO_FILE, sample_rate, recording)

    print("\nRecording completed.")
    print("Saved audio:", RECORDED_AUDIO_FILE)

    return RECORDED_AUDIO_FILE


# ==========================================================
# TEXT CLEANING
# ==========================================================
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_matches(text, words):
    return sum(1 for word in words if word in text)


# ==========================================================
# INTERNAL SCORE CALCULATION
# Scores are used internally for prediction and Groq feedback.
# They are NOT displayed in final output.
# ==========================================================
def calculate_scores(transcript):
    text = clean_text(transcript)
    word_count = len(text.split())

    unclear_terms = [
        "something", "things", "stuff", "maybe", "basic",
        "i think", "i don't know", "not sure", "i forgot",
        "some", "like"
    ]

    if word_count < 20:
        clarity_score = 25
    elif word_count < 45:
        clarity_score = 45
    elif word_count < 90:
        clarity_score = 65
    else:
        clarity_score = 80

    clarity_score -= count_matches(text, unclear_terms) * 4
    clarity_score = max(10, min(100, clarity_score))

    structure_terms = [
        "first", "second", "then", "after that", "finally",
        "because", "for example", "my role was",
        "i was responsible", "the result was", "in conclusion"
    ]

    structure_count = count_matches(text, structure_terms)

    if structure_count == 0:
        structure_score = 20
    elif structure_count == 1:
        structure_score = 45
    elif structure_count <= 3:
        structure_score = 70
    else:
        structure_score = 90

    professional_terms = [
        "developed", "implemented", "designed", "tested", "improved",
        "project", "system", "application", "database", "frontend",
        "backend", "api", "requirements", "team", "user",
        "problem solving", "debugging", "analysis", "solution",
        "figma", "wireframe", "wireframes", "usability testing",
        "python", "java", "react", "node", "sql", "aws",
        "selenium", "postman", "jira", "power bi"
    ]

    professional_count = count_matches(text, professional_terms)

    if professional_count == 0:
        professional_expression_score = 20
    elif professional_count <= 2:
        professional_expression_score = 40
    elif professional_count <= 5:
        professional_expression_score = 65
    else:
        professional_expression_score = 85

    role_terms = [
        "software engineer", "developer", "frontend", "backend",
        "full stack", "qa engineer", "data analyst", "ui ux",
        "ui designer", "ux designer", "cloud engineer", "devops",
        "machine learning engineer", "cyber security", "business analyst",
        "figma", "testing", "python", "java", "sql", "react", "node"
    ]

    role_count = count_matches(text, role_terms)

    if role_count == 0:
        role_alignment_score = 20
    elif role_count <= 2:
        role_alignment_score = 50
    elif role_count <= 5:
        role_alignment_score = 70
    else:
        role_alignment_score = 85

    has_intro = any(x in text for x in ["my name", "myself", "i am", "i'm"])
    has_skills = professional_count >= 2
    has_project = any(x in text for x in ["project", "system", "application", "prototype"])
    has_role = role_count > 0
    has_result = any(x in text for x in ["result", "improved", "completed", "tested", "fixed", "solved"])

    completeness_score = sum([
        has_intro,
        has_skills,
        has_project,
        has_role,
        has_result
    ]) * 20

    final_score = int(
        clarity_score * 0.25
        + structure_score * 0.20
        + professional_expression_score * 0.20
        + role_alignment_score * 0.15
        + completeness_score * 0.20
    )

    final_score = max(0, min(100, final_score))

    return {
        "clarity_score": clarity_score,
        "structure_score": structure_score,
        "professional_expression_score": professional_expression_score,
        "role_alignment_score": role_alignment_score,
        "completeness_score": completeness_score,
        "final_score": final_score
    }


# ==========================================================
# LABEL HELPERS
# ==========================================================
def model_label_to_text(label):
    label = str(label).lower().strip()

    label_map = {
        "1": "poor",
        "2": "average",
        "3": "good",
        "4": "excellent",
        "poor": "poor",
        "average": "average",
        "good": "good",
        "excellent": "excellent"
    }

    return label_map.get(label, "unknown")


def score_label(final_score):
    if final_score < 50:
        return "poor"
    elif final_score < 65:
        return "average"
    elif final_score < 80:
        return "good"
    else:
        return "excellent"


def label_to_number(label):
    label = str(label).lower()

    if label == "poor":
        return 1
    if label == "average":
        return 2
    if label == "good":
        return 3
    if label == "excellent":
        return 4

    return 0


def format_skill_level(label):
    label = str(label).lower()

    if label == "poor":
        return "Poor Communication"
    if label == "average":
        return "Average Communication"
    if label == "good":
        return "Good Communication"
    if label == "excellent":
        return "Excellent Communication"

    return "Unknown Communication Level"


# ==========================================================
# GROQ FEEDBACK GENERATION
# ==========================================================
def generate_groq_feedback(transcript, communication_skill_level, scores):
    prompt = f"""
You are an interview communication coach.

Analyze the candidate's spoken interview answer and generate personalized feedback.

Transcript:
{transcript}

Predicted Communication Skill Level:
{communication_skill_level}

Internal Scores:
Clarity Score: {scores["clarity_score"]}
Structure Score: {scores["structure_score"]}
Professional Expression Score: {scores["professional_expression_score"]}
Role Alignment Score: {scores["role_alignment_score"]}
Completeness Score: {scores["completeness_score"]}
Final Score: {scores["final_score"]}

Return ONLY valid JSON using this exact structure:
{{
  "feedback": "one useful feedback paragraph",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3", "suggestion 4"],
  "better_answer_example": "a better interview answer example"
}}

Rules:
- Do not mention the internal scores in the final feedback.
- Do not give generic feedback.
- Feedback must match the transcript.
- Keep the language simple and useful for students/job seekers.
- Suggestions must improve spoken English, interview structure, professional wording, confidence, and job-role alignment.
- The better answer example must be based on the same role/project mentioned in the transcript.
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You generate valid JSON only for interview communication feedback."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content
        return json.loads(result_text)

    except Exception as error:
        print("Groq feedback generation failed:", error)
        return {
            "feedback": "Feedback generation failed. Please check the Groq API key, internet connection, or model availability.",
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
            "better_answer_example": ""
        }


# ==========================================================
# FULL LIVE PIPELINE
# ==========================================================
def run_live_pipeline(duration=30):
    audio_file = record_live_audio(duration=duration)

    print("\nConverting live audio to text...")
    transcription_result = whisper_model.transcribe(audio_file)
    transcript = transcription_result["text"].strip()

    if not transcript:
        print("No speech detected. Please try again.")
        return None

    cleaned_text = clean_text(transcript)
    scores = calculate_scores(transcript)

    model_input = pd.DataFrame([{
        "clean_transcript": cleaned_text,
        "clarity_score": scores["clarity_score"],
        "structure_score": scores["structure_score"],
        "professional_expression_score": scores["professional_expression_score"]
    }])

    try:
        raw_model_label = communication_model.predict(model_input)[0]
        model_label = model_label_to_text(raw_model_label)
    except Exception as error:
        print("Model prediction failed:", error)
        model_label = "unknown"

    scoring_label = score_label(scores["final_score"])

    if scores["final_score"] < 45:
        final_label = "poor"
    elif model_label != "unknown":
        final_label = model_label
    else:
        final_label = scoring_label

    predicted_level = label_to_number(final_label)
    communication_skill_level = format_skill_level(final_label)

    print("\nGenerating personalized feedback using Groq...")
    ai_feedback = generate_groq_feedback(
        transcript=transcript,
        communication_skill_level=communication_skill_level,
        scores=scores
    )

    output = {
        "transcript": transcript,
        "predicted_level": predicted_level,
        "communication_skill_level": communication_skill_level,
        "feedback": ai_feedback.get("feedback", ""),
        "strengths": ai_feedback.get("strengths", []),
        "weaknesses": ai_feedback.get("weaknesses", []),
        "suggestions": ai_feedback.get("suggestions", []),
        "better_answer_example": ai_feedback.get("better_answer_example", "")
    }

    return output


# ==========================================================
# SAVE + DISPLAY OUTPUT
# ==========================================================
def save_json(output):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = os.path.join(
        OUTPUT_FOLDER,
        f"live_communication_skill_result_{timestamp}.json"
    )

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=4)

    print("\nJSON output saved:")
    print(output_file)


def display_output(output):
    print("\n===================================")
    print("FINAL LIVE COMMUNICATION SKILL OUTPUT")
    print("===================================")

    print("Transcript:", output["transcript"])
    print("Predicted Level:", output["predicted_level"])
    print("Skill Level:", output["communication_skill_level"])

    print("\nFeedback:")
    print(output["feedback"])

    print("\nStrengths:")
    for item in output["strengths"]:
        print("-", item)

    print("\nWeaknesses:")
    for item in output["weaknesses"]:
        print("-", item)

    print("\nSuggestions:")
    for item in output["suggestions"]:
        print("-", item)

    print("\nBetter Answer Example:")
    print(output["better_answer_example"])


# ==========================================================
# MAIN
# ==========================================================
def main():
    print("===================================")
    print("LIVE INTERVIEW COMMUNICATION PIPELINE")
    print("===================================")
    print("This will record your voice, transcribe it, predict the communication level,")
    print("generate personalized feedback, and save the output as JSON.")

    input("\nPress ENTER to start live recording...")

    output = run_live_pipeline(duration=30)

    if output:
        save_json(output)
        display_output(output)


if __name__ == "__main__":
    main()