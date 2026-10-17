import pandas as pd

from ml.config import (
    TRANSCRIPTS_FILE,
    VALIDATED_LABELS_FILE,
    FEATURE_TABLE_FILE,
)
from ml.feature_builder import build_numeric_features


def main():
    print("\n========================================")
    print("BUILD NLP + SPOKEN AUDIO FEATURES")
    print("========================================")

    if not TRANSCRIPTS_FILE.exists():
        raise FileNotFoundError(
            f"Whisper transcript file not found: {TRANSCRIPTS_FILE}\n"
            "Run: python -m training.02_transcribe_training_audio"
        )
    if not VALIDATED_LABELS_FILE.exists():
        raise FileNotFoundError(
            f"Validated label file not found: {VALIDATED_LABELS_FILE}\n"
            "Run: python -m training.01_validate_dataset"
        )

    transcripts = pd.read_csv(TRANSCRIPTS_FILE)
    labels = pd.read_csv(VALIDATED_LABELS_FILE)

    required_transcripts = {"audio_file", "audio_path", "transcript"}
    required_labels = {"audio_file", "label"}
    missing_t = required_transcripts - set(transcripts.columns)
    missing_l = required_labels - set(labels.columns)
    if missing_t:
        raise ValueError("Missing transcript columns: " + ", ".join(sorted(missing_t)))
    if missing_l:
        raise ValueError("Missing label columns: " + ", ".join(sorted(missing_l)))

    transcripts["_audio_key"] = transcripts["audio_file"].astype(str).str.strip().str.lower()
    labels["_audio_key"] = labels["audio_file"].astype(str).str.strip().str.lower()
    labels = labels.drop_duplicates(subset=["_audio_key"], keep="first")

    merged = transcripts.merge(
        labels[["_audio_key", "label"]],
        on="_audio_key",
        how="inner",
    ).drop(columns=["_audio_key"])

    if merged.empty:
        raise RuntimeError("No transcript rows matched validated labels.")

    merged["label"] = merged["label"].astype(str).str.strip().str.lower()
    allowed = {"poor", "average", "good", "excellent"}
    invalid = merged[~merged["label"].isin(allowed)]
    if not invalid.empty:
        raise ValueError("Only poor, average, good, excellent labels are allowed.")

    print(f"\nMatched labelled transcripts: {len(merged)}")
    print("\nCommunication class distribution:")
    print(merged["label"].value_counts())

    output_rows = []
    total = len(merged)
    for position, (_, row) in enumerate(merged.iterrows(), start=1):
        print(f"[{position}/{total}] Processing: {row['audio_file']}")
        try:
            features = build_numeric_features(
                str(row["transcript"]),
                str(row["audio_path"]),
            )
            output_rows.append({
                "audio_file": str(row["audio_file"]),
                "audio_path": str(row["audio_path"]),
                "transcript": str(row["transcript"]),
                "label": str(row["label"]),
                **features,
            })
        except Exception as error:
            print(f"   ERROR: {error}")

    if not output_rows:
        raise RuntimeError("No training features were successfully created.")

    feature_df = pd.DataFrame(output_rows)
    feature_df.to_csv(FEATURE_TABLE_FILE, index=False, encoding="utf-8")

    print("\n========================================")
    print("FEATURE EXTRACTION COMPLETE")
    print("========================================")
    print(f"\nSuccessful feature rows: {len(feature_df)}")
    print(f"Saved to:\n{FEATURE_TABLE_FILE}")


if __name__ == "__main__":
    main()
