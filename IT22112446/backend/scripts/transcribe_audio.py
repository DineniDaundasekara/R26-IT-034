import os
import re
import shutil
import subprocess
import pandas as pd
import imageio_ffmpeg

# ==========================================================
# FFmpeg Setup for Whisper and Audio Conversion
# ==========================================================
IMAGEIO_FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

TOOLS_FOLDER = "tools"
LOCAL_FFMPEG_EXE = os.path.join(TOOLS_FOLDER, "ffmpeg.exe")

os.makedirs(TOOLS_FOLDER, exist_ok=True)

# Copy imageio ffmpeg as ffmpeg.exe because Whisper searches for "ffmpeg"
if not os.path.exists(LOCAL_FFMPEG_EXE):
    shutil.copyfile(IMAGEIO_FFMPEG_EXE, LOCAL_FFMPEG_EXE)

TOOLS_ABSOLUTE_PATH = os.path.abspath(TOOLS_FOLDER)
os.environ["PATH"] = TOOLS_ABSOLUTE_PATH + os.pathsep + os.environ["PATH"]

print("Using FFmpeg:", os.path.abspath(LOCAL_FFMPEG_EXE))

import whisper

# ==========================================================
# PATH SETTINGS
# ==========================================================
AUDIO_FOLDER = "../audio/input"
OUTPUT_FILE = "../audio/label/interview_dataset.csv"

# Change this range when adding new audio files
# Example: 25 to 30 means 25.mpeg/25.ogg/25.wav until 30.mpeg/30.ogg/30.wav
START_NO = 221
END_NO = 248


# Supported input audio/video formats
SUPPORTED_FORMATS = [
    ".wav",
    ".ogg",
    ".mpeg",
    ".mp3",
    ".m4a",
    ".webm",
    ".aac",
    ".flac",
    ".wma",
    ".mp4",
    ".mov"
]

# ==========================================================
# LOAD WHISPER MODEL
# ==========================================================
model = whisper.load_model("base")


# ==========================================================
# CONVERT ANY AUDIO FORMAT TO WAV
# ==========================================================
def convert_audio_to_wav():
    print("\n========================================")
    print("Audio to WAV Conversion Started")
    print("========================================")

    if not os.path.exists(AUDIO_FOLDER):
        print(f"Audio folder not found: {AUDIO_FOLDER}")
        return

    for number in range(START_NO, END_NO + 1):
        wav_file = os.path.join(AUDIO_FOLDER, f"{number}.wav")

        # If WAV already exists, no need to convert
        if os.path.exists(wav_file):
            print(f"Already exists: {number}.wav")
            continue

        input_file = None

        # Search for supported input file
        for ext in SUPPORTED_FORMATS:
            possible_file = os.path.join(AUDIO_FOLDER, f"{number}{ext}")

            if os.path.exists(possible_file):
                input_file = possible_file
                break

        if input_file is None:
            print(f"Missing audio file for number: {number}")
            continue

        print(f"Converting {os.path.basename(input_file)} to {number}.wav")

        command = [
            LOCAL_FFMPEG_EXE,
            "-y",
            "-i", input_file,
            "-ac", "1",
            "-ar", "16000",
            wav_file
        ]

        try:
            subprocess.run(command, check=True)
            print(f"Converted successfully: {number}.wav")
        except subprocess.CalledProcessError as e:
            print(f"Error converting {os.path.basename(input_file)}: {e}")

    print("Audio to WAV conversion completed.")


# ==========================================================
# TEXT CLEANING
# ==========================================================
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ==========================================================
# COMMUNICATION SCORE CALCULATION
# ==========================================================
def calculate_scores(text):
    text = clean_text(text)
    words = text.split()
    word_count = len(words)

    # 1. Clarity score based on answer length
    if word_count < 20:
        clarity_score = 30
    elif word_count < 50:
        clarity_score = 55
    elif word_count < 100:
        clarity_score = 75
    else:
        clarity_score = 90

    # 2. Structure score
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

    # 3. Professional expression score
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

    # 4. Weak words penalty
    weak_words = [
        "i don't know",
        "not sure",
        "maybe",
        "something",
        "like",
        "um",
        "uh",
        "actually"
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
# LABEL ASSIGNMENT
# ==========================================================
def assign_label(final_score):
    if final_score < 40:
        return "poor"
    elif final_score < 60:
        return "average"
    elif final_score < 80:
        return "good"
    else:
        return "excellent"


# ==========================================================
# FEEDBACK GENERATION
# ==========================================================
def generate_feedback(label, clarity, structure, professional):
    feedback = []

    if clarity < 60:
        feedback.append("Answer is too short or not clear enough.")
    else:
        feedback.append("Answer has acceptable clarity.")

    if structure < 60:
        feedback.append("Improve answer structure using First, Then, Finally or STAR method.")
    else:
        feedback.append("Answer has good structure.")

    if professional < 60:
        feedback.append(
            "Use more professional words related to skills, projects, teamwork, and experience."
        )
    else:
        feedback.append("Professional expression is good.")

    if label == "poor":
        feedback.append("Overall communication level needs improvement.")
    elif label == "average":
        feedback.append("Overall communication is understandable but needs better structure.")
    elif label == "good":
        feedback.append("Overall communication is good and suitable for interview practice.")
    else:
        feedback.append("Overall communication is excellent and well prepared.")

    return " ".join(feedback)


# ==========================================================
# GET WAV FILES FROM SELECTED RANGE
# ==========================================================
def get_wav_files_by_range():
    wav_files = []

    if not os.path.exists(AUDIO_FOLDER):
        print(f"Audio folder not found: {AUDIO_FOLDER}")
        return wav_files

    for number in range(START_NO, END_NO + 1):
        wav_file_name = f"{number}.wav"
        wav_file_path = os.path.join(AUDIO_FOLDER, wav_file_name)

        if os.path.exists(wav_file_path):
            wav_files.append(wav_file_name)
        else:
            print(f"Missing WAV file after conversion: {wav_file_name}")

    return wav_files


# ==========================================================
# TRANSCRIBE WAV TO TEXT AND SAVE CSV
# ==========================================================
def transcribe_audio_to_csv():
    print("\n========================================")
    print("Interview Audio Transcription Started")
    print("========================================")
    print(f"Processing range: {START_NO}.wav to {END_NO}.wav")

    if os.path.exists(OUTPUT_FILE):
        existing_df = pd.read_csv(OUTPUT_FILE)
        existing_files = set(existing_df["audio_file"].astype(str))
        print(f"Existing dataset found with {len(existing_df)} records.")
    else:
        existing_df = pd.DataFrame()
        existing_files = set()
        print("No existing dataset found. A new dataset will be created.")

    wav_files = get_wav_files_by_range()

    if not wav_files:
        print("No WAV files found for transcription.")
        return

    print("\nFiles ready for transcription:")
    for file in wav_files:
        print(f" - {file}")

    results = []

    for audio_file in wav_files:
        if audio_file in existing_files:
            print(f"Skipping already processed file: {audio_file}")
            continue

        audio_path = os.path.join(AUDIO_FOLDER, audio_file)

        print(f"\nTranscribing: {audio_file}")

        try:
            result = model.transcribe(audio_path)
            transcript = result["text"].strip()

            clarity, structure, professional, final_score = calculate_scores(transcript)
            label = assign_label(final_score)
            feedback = generate_feedback(label, clarity, structure, professional)

            results.append({
                "audio_file": audio_file,
                "transcript": transcript,
                "clarity_score": clarity,
                "structure_score": structure,
                "professional_expression_score": professional,
                "final_score": final_score,
                "label": label,
                "feedback": feedback
            })

            print(f"Completed: {audio_file}")
            print(f"Transcript: {transcript}")
            print(f"Final Score: {final_score}")
            print(f"Label: {label}")

        except Exception as e:
            print(f"Error processing {audio_file}: {e}")

    new_df = pd.DataFrame(results)

    if new_df.empty:
        print("\nNo new files were processed.")
        return

    if not existing_df.empty:
        final_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        final_df = new_df

    final_df = final_df.drop_duplicates(subset=["audio_file"], keep="last")

    final_df["file_number"] = final_df["audio_file"].apply(
        lambda x: int(os.path.splitext(str(x))[0])
    )

    final_df = final_df.sort_values("file_number")
    final_df = final_df.drop(columns=["file_number"])

    os.makedirs("audio/label", exist_ok=True)

    final_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("\n========================================")
    print("Audio converted to text successfully!")
    print("Transcription and auto-labeling completed!")
    print("========================================")
    print(f"Saved file: {OUTPUT_FILE}")

    print("\nNewly processed files:")
    print(new_df[["audio_file", "final_score", "label"]])

    print("\nFull dataset summary:")
    print(final_df[["audio_file", "final_score", "label"]])


# ==========================================================
# MAIN
# ==========================================================
if __name__ == "__main__":
    convert_audio_to_wav()
    transcribe_audio_to_csv()