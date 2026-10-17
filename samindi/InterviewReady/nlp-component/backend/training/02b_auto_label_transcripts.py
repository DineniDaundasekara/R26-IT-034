"""Optional provisional labelling helper.

IMPORTANT: these are rubric-based provisional labels, not ground truth.
Review them before training and use expert validation where possible.
"""

import hashlib
import re

import pandas as pd

from ml.config import LABEL_DIR

INPUT_FILE = LABEL_DIR / "interview_dataset_to_label.csv"
OUTPUT_FILE = LABEL_DIR / "interview_dataset_autolabeled.csv"

ACTION_VERBS = {
    "developed", "implemented", "designed", "created", "built", "integrated",
    "tested", "managed", "resolved", "improved", "automated", "configured",
    "deployed", "prepared", "planned", "analysed", "analyzed", "collaborated",
    "contributed", "worked", "fixed", "solved",
}
RESULT_TERMS = {
    "result", "results", "outcome", "achieved", "improved", "reduced", "increased",
    "completed", "successfully", "faster", "clearer", "easier", "accuracy", "reliable",
    "reliability", "quality", "learned", "learnt",
}
PROFESSIONAL_TERMS = {
    "responsible", "responsibility", "contribution", "experience", "project", "implemented",
    "developed", "designed", "tested", "collaborated", "solution", "technical", "team",
    "challenge", "requirement", "integration", "professional",
}
CONTEXT_TERMS = {
    "during", "project", "internship", "experience", "worked", "application", "system",
    "portal", "dashboard",
}
TASK_PHRASES = {
    "responsible", "responsibility", "my part", "my role", "my contribution",
    "main contribution", "task", "assigned",
}
WEAK_LANGUAGE = {
    "i like it", "i think i can", "not expert", "my talking is not", "communication is weak",
    "not speaking professional", "i forgot words", "forget words", "get nervous", "i confused",
}


def normalize_text(text):
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def words(text):
    return re.findall(r"\b[a-z']+\b", normalize_text(text))


def contains_any(text, phrases):
    value = normalize_text(text)
    return any(phrase in value for phrase in phrases)


def transcript_group(text):
    return hashlib.sha1(normalize_text(text).encode("utf-8")).hexdigest()[:12]


def auto_label(transcript):
    token_list = words(transcript)
    word_count = len(token_list)
    action_count = sum(word in ACTION_VERBS for word in token_list)
    result_count = sum(word in RESULT_TERMS for word in token_list)
    professional_count = sum(word in PROFESSIONAL_TERMS for word in token_list)
    has_context = contains_any(transcript, CONTEXT_TERMS)
    has_task = contains_any(transcript, TASK_PHRASES)
    has_weak_language = contains_any(transcript, WEAK_LANGUAGE)

    if (
        word_count >= 90
        and has_context
        and has_task
        and action_count > 0
        and result_count > 0
        and professional_count >= 2
        and not has_weak_language
    ):
        return "excellent"

    if (
        word_count >= 60
        and has_context
        and action_count > 0
        and result_count > 0
        and professional_count >= 2
    ):
        return "good"

    if word_count >= 40 and has_context and (has_task or action_count > 0 or result_count > 0):
        return "average"

    return "poor"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input not found: {INPUT_FILE}\nRun training.02_transcribe_training_audio first."
        )

    df = pd.read_csv(INPUT_FILE)
    if not {"audio_file", "transcript"}.issubset(df.columns):
        raise ValueError("Input must contain audio_file and transcript columns.")

    df["auto_label"] = df["transcript"].apply(auto_label)
    df["final_label"] = df["auto_label"]
    df["transcript_group"] = df["transcript"].apply(transcript_group)
    counts = df["transcript_group"].value_counts()
    duplicate_groups = set(counts[counts > 1].index)
    df["duplicate_transcript"] = df["transcript_group"].isin(duplicate_groups)
    df["review_status"] = "needs_review"

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("\nRubric-based provisional labels:")
    print(df["auto_label"].value_counts())
    print(f"\nRows in exact duplicate groups: {int(df['duplicate_transcript'].sum())}")
    print(f"\nSaved to:\n{OUTPUT_FILE}")
    print("\nReview final_label manually before training. These are not ground-truth labels.")


if __name__ == "__main__":
    main()
