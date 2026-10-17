import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CV_FOLDER = os.path.join(BASE_DIR, "data", "cvs")
LABEL_FILE = os.path.join(BASE_DIR, "data", "cv_labels.csv")

ALLOWED_LABELS = [
    "Software Engineer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "QA Engineer",
    "Data Analyst",
    "UI UX Designer",
    "Cloud Engineer",
    "DevOps Engineer",
    "Business Analyst",
    "Cyber Security Analyst",
    "Machine Learning Engineer"
]


def main():
    print("===================================")
    print("CV LABEL VALIDATION STARTED")
    print("===================================")

    if not os.path.exists(LABEL_FILE):
        print("cv_labels.csv not found.")
        return

    labels_df = pd.read_csv(LABEL_FILE)

    if "file_name" not in labels_df.columns or "career_path_label" not in labels_df.columns:
        print("cv_labels.csv must contain file_name and career_path_label columns.")
        return

    labels_df["file_name"] = labels_df["file_name"].astype(str).str.strip()
    labels_df["career_path_label"] = labels_df["career_path_label"].astype(str).str.strip()

    empty_labels = labels_df[
        (labels_df["career_path_label"] == "")
        | (labels_df["career_path_label"].str.lower() == "nan")
    ]

    invalid_labels = labels_df[
        ~labels_df["career_path_label"].isin(ALLOWED_LABELS)
    ]

    missing_files = []

    for file_name in labels_df["file_name"]:
        cv_path = os.path.join(CV_FOLDER, file_name)

        if not os.path.exists(cv_path):
            missing_files.append(file_name)

    print("Total label rows:", len(labels_df))
    print("Empty labels:", len(empty_labels))
    print("Invalid labels:", len(invalid_labels))
    print("Missing PDF files:", len(missing_files))

    print("\nLabel distribution:")
    print(labels_df["career_path_label"].value_counts())

    if len(empty_labels) > 0:
        print("\nEmpty label examples:")
        print(empty_labels.head())

    if len(invalid_labels) > 0:
        print("\nInvalid label examples:")
        print(invalid_labels.head())

        print("\nAllowed labels:")
        for label in ALLOWED_LABELS:
            print("-", label)

    if missing_files:
        print("\nMissing PDF file examples:")
        for item in missing_files[:10]:
            print("-", item)

    if len(empty_labels) == 0 and len(invalid_labels) == 0 and len(missing_files) == 0:
        print("\nSUCCESS: cv_labels.csv is ready for training.")
    else:
        print("\nPlease fix cv_labels.csv before training.")


if __name__ == "__main__":
    main()