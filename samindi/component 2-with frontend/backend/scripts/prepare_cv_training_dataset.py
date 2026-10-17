import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXTRACTED_TEXT_FILE = os.path.join(BASE_DIR, "data", "cv_extracted_text.csv")
LABEL_FILE = os.path.join(BASE_DIR, "data", "cv_labels.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "cv_training_dataset.csv")

MIN_RECORDS_PER_LABEL = 5


def main():
    print("===================================")
    print("CV TRAINING DATASET PREPARATION")
    print("===================================")

    if not os.path.exists(EXTRACTED_TEXT_FILE):
        print("cv_extracted_text.csv not found. Run extract_cv_sections.py first.")
        return

    if not os.path.exists(LABEL_FILE):
        print("cv_labels.csv not found. Run auto_label_cvs.py first.")
        return

    extracted_df = pd.read_csv(EXTRACTED_TEXT_FILE)
    labels_df = pd.read_csv(LABEL_FILE)

    extracted_df["file_name"] = extracted_df["file_name"].astype(str).str.strip()
    labels_df["file_name"] = labels_df["file_name"].astype(str).str.strip()
    labels_df["career_path_label"] = labels_df["career_path_label"].astype(str).str.strip()

    labels_df = labels_df[
        (labels_df["career_path_label"] != "")
        & (labels_df["career_path_label"].str.lower() != "nan")
    ]

    merged_df = pd.merge(
        extracted_df,
        labels_df,
        on="file_name",
        how="inner"
    )

    required_columns = [
        "skills", "projects", "education", "tools",
        "experience", "certifications"
    ]

    for column in required_columns:
        if column not in merged_df.columns:
            merged_df[column] = ""

    merged_df = merged_df.dropna(subset=["cv_text", "career_path_label"])
    merged_df = merged_df[merged_df["cv_text"].astype(str).str.len() > 50]

    merged_df["combined_training_text"] = (
        merged_df["skills"].fillna("") + " " +
        merged_df["projects"].fillna("") + " " +
        merged_df["education"].fillna("") + " " +
        merged_df["tools"].fillna("") + " " +
        merged_df["experience"].fillna("") + " " +
        merged_df["certifications"].fillna("") + " " +
        merged_df["cv_text"].fillna("")
    )

    label_counts = merged_df["career_path_label"].value_counts()
    valid_labels = label_counts[label_counts >= MIN_RECORDS_PER_LABEL].index.tolist()

    filtered_df = merged_df[
        merged_df["career_path_label"].isin(valid_labels)
    ]

    if filtered_df.empty:
        print("No training records created.")
        print("Check file_name matching and labels.")
        return

    filtered_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("Training dataset created successfully.")
    print("Extracted CV records:", len(extracted_df))
    print("Label records:", len(labels_df))
    print("Records before filtering:", len(merged_df))
    print("Final training records:", len(filtered_df))
    print("Saved:", OUTPUT_FILE)

    print("\nLabels used for training:")
    print(filtered_df["career_path_label"].value_counts())

    removed_labels = label_counts[label_counts < MIN_RECORDS_PER_LABEL]

    if not removed_labels.empty:
        print("\nLabels removed because they have fewer than 5 records:")
        print(removed_labels)


if __name__ == "__main__":
    main()