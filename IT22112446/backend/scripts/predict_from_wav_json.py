import os
import re
import sys
import json
import time
import shutil
import warnings

import pandas as pd
import joblib
import imageio_ffmpeg
from dotenv import load_dotenv
from groq import Groq

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# ==========================================================
# PATH SETTINGS
# ==========================================================
MODEL_FILE = "../models/best_communication_skill_model.pkl"
AUDIO_FOLDER = "../audio/input"
OUTPUT_FOLDER = "../outputs"
ENV_FILE = "../.env"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Full dataset starts from this audio number
START_AUDIO_NUMBER = 138

# Use smaller model to reduce Groq token usage
GROQ_MODEL = "llama-3.1-8b-instant"

# Avoid sending same files again to Groq if JSON already exists
SKIP_EXISTING_JSON = True

# Small delay for batch processing
API_DELAY_SECONDS = 2

# Run examples:
# python predict_from_wav_json.py 138   -> process only 138.wav
# python predict_from_wav_json.py       -> process all .wav files from 138.wav

DEFAULT_AUDIO_NUMBER = 138

if len(sys.argv) > 1:
    AUDIO_NUMBER = int(sys.argv[1])
else:
    AUDIO_NUMBER = DEFAULT_AUDIO_NUMBER

AUDIO_FILE = os.path.join(AUDIO_FOLDER, f"{AUDIO_NUMBER}.wav")
OUTPUT_JSON_FILE = os.path.join(
    OUTPUT_FOLDER,
    f"communication_skill_result_{AUDIO_NUMBER}.json"
)

# ==========================================================
# LOAD ENV + GROQ CLIENT
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
# Scores are used internally only.
# They are NOT displayed in final JSON.
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
        "selenium", "postman", "jira", "power bi", "linux", "terraform"
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
        "figma", "testing", "python", "java", "sql", "react", "node",
        "aws", "linux", "terraform"
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
    has_project = any(x in text for x in ["project", "system", "application", "prototype", "dashboard"])
    has_role = role_count > 0
    has_result = any(x in text for x in ["result", "improved", "completed", "tested", "fixed", "solved", "easier"])

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
# FALLBACK FEEDBACK
# Used when Groq rate limit happens.
# This prevents empty feedback in JSON.
# ==========================================================
def fallback_feedback(transcript, communication_skill_level):
    text = clean_text(transcript)

    strengths = []
    weaknesses = []
    suggestions = []

    if any(word in text for word in ["aws", "linux", "terraform", "python", "java", "figma", "sql", "react"]):
        strengths.append("The answer includes some relevant technical skills.")

    if any(word in text for word in ["project", "system", "dashboard", "application"]):
        strengths.append("The candidate mentions project experience, which is useful for interview discussion.")

    if not strengths:
        strengths.append("The candidate attempted to answer the interview question.")

    if "my role was" not in text and "my part was" not in text and "i was responsible" not in text:
        weaknesses.append("The answer should explain the candidate's exact responsibility more clearly.")

    if not any(word in text for word in ["first", "then", "finally", "because", "result"]):
        weaknesses.append("The answer needs a clearer structure and flow.")

    if len(text.split()) < 60:
        weaknesses.append("The answer needs more detail about skills, project work, and final outcome.")

    suggestions.append("Use a clear structure: introduction, target role, skills, project, contribution, and result.")
    suggestions.append("Explain your exact project responsibility using professional words.")
    suggestions.append("Connect your skills directly to the selected job role.")
    suggestions.append("End with a confident sentence about why you are suitable for the role.")

    if "cloud" in text or "aws" in text or "terraform" in text:
        better_answer = (
            "My name is Amanda. I am a computing graduate preparing for a Cloud Engineer role. "
            "I have practiced AWS, Linux, and Terraform. In my sales dashboard project, I worked on the reporting part, "
            "where I helped organize sales data and make reports easier to understand. This project improved my technical "
            "skills, problem-solving ability, and understanding of business requirements. I want to continue improving my "
            "cloud engineering skills and contribute to real-world cloud solutions."
        )
    else:
        better_answer = (
            "My name is Amanda. I am an IT graduate preparing for an IT-related role. "
            "I have practiced technical skills through academic projects. In my project, I worked on understanding requirements, "
            "developing features, and testing the system. This helped me improve my communication, teamwork, and problem-solving skills. "
            "I believe these skills match the role I am applying for."
        )

    return {
        "feedback": (
            f"The predicted level is {communication_skill_level}. The answer contains useful information, "
            "but it needs clearer structure, stronger professional wording, and more detail about the candidate's role and project outcome."
        ),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "better_answer_example": better_answer
    }


# ==========================================================
# GROQ FEEDBACK GENERATION
# ==========================================================
def generate_groq_feedback(transcript, communication_skill_level, scores):
    short_transcript = transcript[:900]

    prompt = f"""
Analyze this interview answer and return ONLY valid JSON.

Transcript:
{short_transcript}

Predicted Level:
{communication_skill_level}

Internal scores:
clarity={scores["clarity_score"]}, structure={scores["structure_score"]},
professional={scores["professional_expression_score"]},
role_alignment={scores["role_alignment_score"]}, completeness={scores["completeness_score"]}

JSON format:
{{
  "feedback": "one useful feedback paragraph",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3", "suggestion 4"],
  "better_answer_example": "a better interview answer example"
}}

Rules:
- Do not mention scores.
- Make feedback specific to the transcript.
- Use simple student-friendly English.
- Better answer must match the same role/project.
"""

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=450,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content
        return json.loads(result_text)

    except Exception as error:
        print("Groq feedback generation failed:", error)
        print("Using local fallback feedback instead.")
        return fallback_feedback(transcript, communication_skill_level)


# ==========================================================
# GET ALL WAV FILES FROM 138.WAV
# ==========================================================
def get_all_wav_files():
    wav_files = []

    if not os.path.exists(AUDIO_FOLDER):
        print("Audio folder not found:", os.path.abspath(AUDIO_FOLDER))
        return wav_files

    for file_name in os.listdir(AUDIO_FOLDER):
        if file_name.lower().endswith(".wav"):
            file_number_text = os.path.splitext(file_name)[0]

            if file_number_text.isdigit():
                file_number = int(file_number_text)

                if file_number >= START_AUDIO_NUMBER:
                    wav_files.append(os.path.join(AUDIO_FOLDER, file_name))

    wav_files = sorted(
        wav_files,
        key=lambda path: int(os.path.splitext(os.path.basename(path))[0])
    )

    return wav_files


# ==========================================================
# PREDICT FROM WAV
# ==========================================================
def predict_from_wav(audio_file):
    if not os.path.exists(audio_file):
        print("Audio file not found:", os.path.abspath(audio_file))
        return None

    print("Input WAV file:", audio_file)
    print("Transcribing WAV audio...")

    try:
        transcription_result = whisper_model.transcribe(audio_file)
        transcript = transcription_result["text"].strip()
    except Exception as error:
        print("Transcription failed:", error)
        return None

    if not transcript:
        print("No speech detected in the audio.")
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

    ai_feedback = generate_groq_feedback(
        transcript=transcript,
        communication_skill_level=communication_skill_level,
        scores=scores
    )

    output = {
        "audio_file": os.path.basename(audio_file),
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
# SAVE JSON FILES
# ==========================================================
def get_output_file_for_audio(audio_file):
    audio_name = os.path.basename(audio_file)
    audio_number = os.path.splitext(audio_name)[0]

    return os.path.join(
        OUTPUT_FOLDER,
        f"communication_skill_result_{audio_number}.json"
    )


def save_single_json(output):
    audio_number = os.path.splitext(output["audio_file"])[0]

    output_file = os.path.join(
        OUTPUT_FOLDER,
        f"communication_skill_result_{audio_number}.json"
    )

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=4)

    print("JSON output saved:", output_file)


def save_json(output):
    with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=4)

    print("\nJSON output saved:")
    print(OUTPUT_JSON_FILE)


def load_existing_json(output_file):
    with open(output_file, "r", encoding="utf-8") as file:
        return json.load(file)


# ==========================================================
# DISPLAY OUTPUT
# ==========================================================
def display_output(output):
    print("\n===================================")
    print("FINAL COMMUNICATION SKILL OUTPUT")
    print("===================================")

    if "audio_file" in output:
        print("Audio File:", output["audio_file"])

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
    print("WAV AUDIO COMMUNICATION SKILL TEST")
    print("===================================")

    # One file mode
    if len(sys.argv) > 1:
        output = predict_from_wav(AUDIO_FILE)

        if output:
            save_json(output)
            display_output(output)

        return

    # Full dataset mode from 138.wav
    wav_files = get_all_wav_files()

    if not wav_files:
        print("No WAV files found from", START_AUDIO_NUMBER, "in:", AUDIO_FOLDER)
        return

    print("Starting from:", f"{START_AUDIO_NUMBER}.wav")
    print("Total WAV files found:", len(wav_files))

    all_results = []

    for audio_file in wav_files:
        print("\n-----------------------------------")
        print("Processing:", audio_file)
        print("-----------------------------------")

        output_file = get_output_file_for_audio(audio_file)

        if SKIP_EXISTING_JSON and os.path.exists(output_file):
            print("Existing JSON found. Skipping Groq call:", output_file)
            output = load_existing_json(output_file)
            display_output(output)
            all_results.append(output)
            continue

        output = predict_from_wav(audio_file)

        if output:
            save_single_json(output)
            display_output(output)
            all_results.append(output)

        time.sleep(API_DELAY_SECONDS)

    all_results_file = os.path.join(
        OUTPUT_FOLDER,
        f"all_communication_skill_results_from_{START_AUDIO_NUMBER}.json"
    )

    with open(all_results_file, "w", encoding="utf-8") as file:
        json.dump(all_results, file, indent=4)

    print("\n===================================")
    print("ALL FILES COMPLETED")
    print("===================================")
    print("Started from:", f"{START_AUDIO_NUMBER}.wav")
    print("Total processed files:", len(all_results))
    print("All results saved:", all_results_file)


if __name__ == "__main__":
    main()