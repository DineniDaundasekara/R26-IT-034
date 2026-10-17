from pathlib import Path
import os

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

DATA_DIR = BACKEND_DIR / "data"
TRAINING_AUDIO_DIR = DATA_DIR / "training_audio"
LABEL_DIR = DATA_DIR / "labels"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = BACKEND_DIR / "models"
TEMP_DIR = BACKEND_DIR / "temp"

LABEL_FILE = LABEL_DIR / "interview_dataset.csv"
VALIDATED_LABELS_FILE = PROCESSED_DIR / "validated_labels.csv"
VALIDATION_REPORT_FILE = PROCESSED_DIR / "dataset_validation_report.json"
TRANSCRIPTS_FILE = PROCESSED_DIR / "whisper_transcripts.csv"
FEATURE_TABLE_FILE = PROCESSED_DIR / "training_feature_table.csv"

MODEL_FILE = MODELS_DIR / "communication_pipeline.joblib"
MODEL_METADATA_FILE = MODELS_DIR / "model_metadata.json"
RESEARCH_METRICS_FILE = MODELS_DIR / "research_metrics.json"

ALLOWED_LABELS = ["poor", "average", "good", "excellent"]

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small.en")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_GUIDANCE_MODEL = os.getenv(
    "OPENAI_GUIDANCE_MODEL",
    "gpt-5.6-sol",
).strip()
OPENAI_GUIDANCE_ENABLED = os.getenv(
    "OPENAI_GUIDANCE_ENABLED",
    "true",
).strip().lower() in {"1", "true", "yes", "on"}
OPENAI_GUIDANCE_VERIFY = os.getenv(
    "OPENAI_GUIDANCE_VERIFY",
    "true",
).strip().lower() in {"1", "true", "yes", "on"}
OPENAI_VERIFIER_MODEL = os.getenv(
    "OPENAI_VERIFIER_MODEL",
    OPENAI_GUIDANCE_MODEL,
).strip()

AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".ogg",
    ".webm",
    ".flac",
    ".aac",
}

for path in [
    TRAINING_AUDIO_DIR,
    LABEL_DIR,
    PROCESSED_DIR,
    MODELS_DIR,
    TEMP_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)
