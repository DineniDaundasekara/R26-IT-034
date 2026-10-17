import json
from collections import Counter
from pathlib import Path

import pandas as pd

from ml.config import (
    TRAINING_AUDIO_DIR,
    LABEL_FILE,
    VALIDATED_LABELS_FILE,
    VALIDATION_REPORT_FILE,
    AUDIO_EXTENSIONS,
)
from ml.labels import load_label_dataset


def all_audio_files():
    return sorted(
        path
        for path in TRAINING_AUDIO_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in AUDIO_EXTENSIONS
    )


def build_file_lookup(files):
    exact = {
        path.name.lower(): path
        for path in files
    }

    by_stem = {}

    for path in files:
        by_stem.setdefault(
            path.stem.lower(),
            []
        ).append(path)

    return exact, by_stem


def resolve_audio(name, exact, by_stem):
    supplied = Path(str(name).strip())
    exact_match = exact.get(
        supplied.name.lower()
    )

    if exact_match:
        return exact_match

    stem_matches = by_stem.get(
        supplied.stem.lower(),
        []
    )

    if len(stem_matches) == 1:
        return stem_matches[0]

    return None


def main():
    if not LABEL_FILE.exists():
        raise FileNotFoundError(
            f"Dataset file not found:\n{LABEL_FILE}\n\n"
            "Place your dataset CSV at that exact path."
        )

    files = all_audio_files()

    if not files:
        raise RuntimeError(
            f"No training audio files found in:\n{TRAINING_AUDIO_DIR}"
        )

    labels = load_label_dataset(
        LABEL_FILE
    )

    exact, by_stem = build_file_lookup(
        files
    )

    duplicate_stems = {
        stem: [item.name for item in items]
        for stem, items in by_stem.items()
        if len(items) > 1
    }

    rows = []
    missing_dataset_audio = []

    for _, row in labels.iterrows():
        resolved = resolve_audio(
            row["audio_file"],
            exact,
            by_stem,
        )

        if resolved is None:
            missing_dataset_audio.append(
                str(row["audio_file"])
            )
            continue

        rows.append({
            "audio_file": resolved.name,
            "audio_path": str(
                resolved.resolve()
            ),
            "label": row["label"],
        })

    validated = pd.DataFrame(rows)

    if validated.empty:
        raise RuntimeError(
            "No dataset rows could be matched to audio files."
        )

    duplicated_dataset_files = (
        validated["audio_file"]
        .str.lower()
        .duplicated(keep=False)
    )

    duplicate_dataset_rows = (
        validated.loc[
            duplicated_dataset_files,
            "audio_file"
        ]
        .tolist()
    )

    if duplicate_dataset_rows:
        raise ValueError(
            "The label dataset contains duplicate audio rows: "
            + ", ".join(
                sorted(set(duplicate_dataset_rows))
            )
        )

    referenced = {
        name.lower()
        for name in validated["audio_file"]
    }

    unreferenced_audio = [
        path.name
        for path in files
        if path.name.lower()
        not in referenced
    ]

    class_distribution = {
        str(key): int(value)
        for key, value
        in validated["label"]
        .value_counts()
        .items()
    }

    report = {
        "audio_files_found": len(files),
        "dataset_rows_with_valid_label": len(labels),
        "matched_training_rows": len(validated),
        "missing_audio_named_by_dataset": missing_dataset_audio,
        "audio_files_not_referenced_by_dataset": unreferenced_audio,
        "duplicate_audio_stems_in_folder": duplicate_stems,
        "class_distribution": class_distribution,
    }

    validated.to_csv(
        VALIDATED_LABELS_FILE,
        index=False,
        encoding="utf-8",
    )

    VALIDATION_REPORT_FILE.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nDATASET VALIDATION COMPLETE")
    print("---------------------------")
    print(
        f"Audio files found: {len(files)}"
    )
    print(
        f"Valid dataset rows: {len(labels)}"
    )
    print(
        f"Matched labelled audio: {len(validated)}"
    )

    print("\nClass distribution:")
    print(
        validated["label"]
        .value_counts()
    )

    if missing_dataset_audio:
        print(
            "\nWARNING: Some dataset rows do not have a matching audio file."
        )
        print(
            f"Count: {len(missing_dataset_audio)}"
        )

    if unreferenced_audio:
        print(
            "\nNOTE: Some audio files are not referenced by your dataset and will not be used."
        )
        print(
            f"Count: {len(unreferenced_audio)}"
        )

    if duplicate_stems:
        print(
            "\nNOTE: Duplicate filename stems were found. Exact filename matching is preferred."
        )
        print(
            json.dumps(
                duplicate_stems,
                indent=2,
            )
        )

    print(
        f"\nValidated mapping saved to:\n{VALIDATED_LABELS_FILE}"
    )
    print(
        f"\nFull report saved to:\n{VALIDATION_REPORT_FILE}"
    )


if __name__ == "__main__":
    main()
