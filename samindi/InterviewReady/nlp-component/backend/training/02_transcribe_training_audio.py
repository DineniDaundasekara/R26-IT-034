import argparse
import re
from pathlib import Path

import pandas as pd

from ml.config import (
    LABEL_DIR,
    TRAINING_AUDIO_DIR,
    TRANSCRIPTS_FILE,
    AUDIO_EXTENSIONS,
)
from ml.transcriber import transcribe_audio

LABEL_SHEET_FILE = LABEL_DIR / "interview_dataset_to_label.csv"


def natural_key(path: Path):
    parts = re.split(r"(\d+)", path.name.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def list_audio_files():
    return sorted(
        [
            path
            for path in TRAINING_AUDIO_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
        ],
        key=natural_key,
    )


def load_existing_transcripts():
    if not TRANSCRIPTS_FILE.exists():
        return {}

    data = pd.read_csv(TRANSCRIPTS_FILE)
    if "audio_file" not in data.columns or "transcript" not in data.columns:
        return {}

    return {
        str(row["audio_file"]).strip().lower(): str(row["transcript"] or "")
        for _, row in data.iterrows()
    }


def load_existing_labels():
    if not LABEL_SHEET_FILE.exists():
        return {}

    data = pd.read_csv(LABEL_SHEET_FILE)
    if "audio_file" not in data.columns or "label" not in data.columns:
        return {}

    return {
        str(row["audio_file"]).strip().lower(): str(row["label"] or "").strip()
        for _, row in data.iterrows()
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-transcribe files even if a transcript already exists.",
    )
    args = parser.parse_args()

    print("\n========================================")
    print("WHISPER TRAINING AUDIO TRANSCRIPTION")
    print("========================================\n")

    audio_files = list_audio_files()
    print(f"Audio files found: {len(audio_files)}")

    if not audio_files:
        raise FileNotFoundError(
            f"No supported audio files were found in: {TRAINING_AUDIO_DIR}"
        )

    existing_transcripts = load_existing_transcripts()
    existing_labels = load_existing_labels()
    rows = []

    for index, audio_path in enumerate(audio_files, start=1):
        key = audio_path.name.lower()
        transcript = existing_transcripts.get(key, "")

        if transcript and not args.force:
            print(f"[{index}/{len(audio_files)}] SKIP: {audio_path.name}")
        else:
            print(f"[{index}/{len(audio_files)}] Whisper: {audio_path.name}")
            transcript = transcribe_audio(str(audio_path))

        rows.append({
            "audio_file": audio_path.name,
            "audio_path": str(audio_path.resolve()),
            "transcript": transcript,
        })

        pd.DataFrame(rows).to_csv(
            TRANSCRIPTS_FILE,
            index=False,
            encoding="utf-8",
        )

    transcript_df = pd.DataFrame(rows)
    transcript_df.to_csv(
        TRANSCRIPTS_FILE,
        index=False,
        encoding="utf-8",
    )

    label_df = transcript_df[["audio_file", "transcript"]].copy()
    label_df["label"] = label_df["audio_file"].apply(
        lambda name: existing_labels.get(str(name).lower(), "")
    )
    label_df.to_csv(
        LABEL_SHEET_FILE,
        index=False,
        encoding="utf-8",
    )

    print("\nTranscripts saved to:")
    print(TRANSCRIPTS_FILE)
    print("\nHuman review sheet saved to:")
    print(LABEL_SHEET_FILE)
    print("\nNEXT:")
    print("Review/fill Poor, Average, Good, or Excellent labels, then save final labels as interview_dataset.csv.")


if __name__ == "__main__":
    main()
