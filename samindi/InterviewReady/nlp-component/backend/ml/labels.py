import re
import pandas as pd

from .config import ALLOWED_LABELS


FILE_COLUMN_CANDIDATES = [
    "audio_file",
    "file_name",
    "filename",
    "audio",
    "audio_filename",
]

LABEL_COLUMN_CANDIDATES = [
    "label",
    "communication_level",
    "communicationlevel",
    "class",
    "level",
]


def normalize_column_name(name: str) -> str:
    value = str(name).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def normalize_label(value: str) -> str:
    text = str(value or "").strip().lower()

    aliases = {
        "poor communication": "poor",
        "average communication": "average",
        "good communication": "good",
        "excellent communication": "excellent",
    }

    return aliases.get(text, text)


def find_column(df: pd.DataFrame, candidates):
    normalized = {
        normalize_column_name(column): column
        for column in df.columns
    }

    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]

    return None


def load_label_dataset(csv_path):
    df = pd.read_csv(csv_path)

    file_col = find_column(df, FILE_COLUMN_CANDIDATES)
    label_col = find_column(df, LABEL_COLUMN_CANDIDATES)

    if file_col is None:
        raise ValueError(
            "Could not find an audio filename column. "
            "Use one of: audio_file, file_name, filename, audio, audio_filename."
        )

    if label_col is None:
        raise ValueError(
            "Could not find a label column. "
            "Use one of: label, communication_level, class, level."
        )

    out = pd.DataFrame({
        "audio_file": df[file_col].astype(str).str.strip(),
        "label": df[label_col].map(normalize_label),
    })

    out = out[
        out["audio_file"].ne("")
        & out["label"].ne("")
    ].copy()

    invalid = sorted(
        set(out["label"]) - set(ALLOWED_LABELS)
    )

    if invalid:
        raise ValueError(
            "Invalid communication labels found: "
            + ", ".join(invalid)
            + ". Allowed labels are: "
            + ", ".join(ALLOWED_LABELS)
        )

    return out
