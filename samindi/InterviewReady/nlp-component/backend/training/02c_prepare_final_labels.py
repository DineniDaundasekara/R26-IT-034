import pandas as pd

from ml.config import LABEL_DIR, LABEL_FILE

INPUT_FILE = LABEL_DIR / "interview_dataset_autolabeled.csv"
ALLOWED = {"poor", "average", "good", "excellent"}


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"File not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)
    required = {"audio_file", "final_label"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))

    labels = (
        df["final_label"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    invalid = ~labels.isin(ALLOWED)
    if invalid.any():
        print(df.loc[invalid, ["audio_file", "final_label"]])
        raise ValueError("Invalid or missing final labels found.")

    output = pd.DataFrame({
        "audio_file": df["audio_file"],
        "label": labels,
    })
    output.to_csv(LABEL_FILE, index=False, encoding="utf-8")

    print(f"\nFinal label dataset created:\n{LABEL_FILE}")
    print("\nClass distribution:")
    print(output["label"].value_counts())


if __name__ == "__main__":
    main()
