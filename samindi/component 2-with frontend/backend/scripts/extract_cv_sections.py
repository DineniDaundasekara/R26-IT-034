import os
import re
import pymupdf
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CV_FOLDER = os.path.join(BASE_DIR, "data", "cvs")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "cv_extracted_text.csv")


SECTION_KEYWORDS = {
    "education": [
        "education", "academic qualification", "academic qualifications",
        "qualification", "qualifications", "academic background"
    ],
    "skills": [
        "skills", "technical skills", "soft skills", "key skills",
        "core skills", "professional skills", "competencies"
    ],
    "projects": [
        "projects", "academic projects", "project experience",
        "personal projects", "portfolio", "selected projects"
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "internship", "employment history", "career history"
    ],
    "certifications": [
        "certifications", "certificates", "courses", "training",
        "licenses", "achievements"
    ],
    "tools": [
        "tools", "technologies", "technology stack", "software tools",
        "frameworks", "programming languages", "languages and tools"
    ]
}


def extract_text_from_pdf(pdf_path):
    text = ""

    try:
        document = pymupdf.open(pdf_path)

        for page in document:
            text += page.get_text("text") + "\n"

        document.close()

    except Exception as error:
        print("Error reading PDF:", pdf_path)
        print("Error:", error)

    return text.strip()


def clean_text(text):
    text = str(text)
    text = text.replace("\r", "\n")
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def normalize_heading(line):
    line = str(line).lower().strip()
    line = re.sub(r"[^a-zA-Z\s]", " ", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line


def detect_section_heading(line):
    normalized_line = normalize_heading(line)

    for section_name, keywords in SECTION_KEYWORDS.items():
        for keyword in keywords:
            if normalized_line == keyword:
                return section_name

            if len(normalized_line.split()) <= 4 and keyword in normalized_line:
                return section_name

    return None


def extract_sections(cv_text):
    sections = {
        "education": "",
        "skills": "",
        "projects": "",
        "experience": "",
        "certifications": "",
        "tools": ""
    }

    lines = cv_text.split("\n")
    current_section = None

    for line in lines:
        clean_line = line.strip()

        if not clean_line:
            continue

        detected_section = detect_section_heading(clean_line)

        if detected_section:
            current_section = detected_section
            continue

        if current_section:
            sections[current_section] += clean_line + " "

    for key in sections:
        sections[key] = " ".join(sections[key].split())

    return sections


def extract_candidate_name_hint(cv_text):
    lines = [line.strip() for line in cv_text.split("\n") if line.strip()]

    skip_words = [
        "cv", "resume", "curriculum vitae", "personal details",
        "profile", "email", "phone", "address", "linkedin", "github"
    ]

    for line in lines[:12]:
        lower_line = line.lower()

        if any(word in lower_line for word in skip_words):
            continue

        if any(char.isdigit() for char in line):
            continue

        if 1 <= len(line.split()) <= 5:
            return line

    return ""


def main():
    print("===================================")
    print("CV PDF SECTION EXTRACTION STARTED")
    print("===================================")

    if not os.path.exists(CV_FOLDER):
        print("CV folder not found:", CV_FOLDER)
        return

    pdf_files = [
        file_name for file_name in os.listdir(CV_FOLDER)
        if file_name.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print("No PDF files found in:", CV_FOLDER)
        return

    records = []
    skipped_files = []

    for file_name in pdf_files:
        pdf_path = os.path.join(CV_FOLDER, file_name)

        print("Extracting:", file_name)

        raw_text = extract_text_from_pdf(pdf_path)
        cv_text = clean_text(raw_text)

        if len(cv_text.strip()) < 50:
            skipped_files.append(file_name)
            print("Skipped because extracted text is too short:", file_name)
            continue

        sections = extract_sections(cv_text)
        candidate_name_hint = extract_candidate_name_hint(cv_text)

        records.append({
            "file_name": file_name,
            "candidate_name_hint": candidate_name_hint,
            "cv_text": " ".join(cv_text.split()),
            "skills": sections["skills"],
            "projects": sections["projects"],
            "education": sections["education"],
            "tools": sections["tools"],
            "experience": sections["experience"],
            "certifications": sections["certifications"]
        })

    if not records:
        print("No CV text extracted.")
        return

    output_df = pd.DataFrame(records)
    output_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("\n===================================")
    print("CV SECTION EXTRACTION COMPLETED")
    print("===================================")
    print("Total PDF files found:", len(pdf_files))
    print("Total CV text extracted:", len(output_df))
    print("Skipped PDFs:", len(skipped_files))
    print("Saved file:", OUTPUT_FILE)

    if skipped_files:
        print("\nSkipped files:")
        for file_name in skipped_files:
            print("-", file_name)

    print("\nOutput columns:")
    print(list(output_df.columns))


if __name__ == "__main__":
    main()