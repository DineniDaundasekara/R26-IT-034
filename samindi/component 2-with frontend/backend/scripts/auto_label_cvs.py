import os
import re
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = os.path.join(BASE_DIR, "data", "cv_extracted_text.csv")
AUTO_LABEL_FILE = os.path.join(BASE_DIR, "data", "cv_labels_auto.csv")
FINAL_LABEL_FILE = os.path.join(BASE_DIR, "data", "cv_labels.csv")


ROLE_KEYWORDS = {
    "Software Engineer": [
        "software engineer", "software development", "programming",
        "java", "python", "javascript", "spring boot", "oop",
        "rest api", "rest apis", "application development",
        "system development", "github", "git", "web application"
    ],

    "Frontend Developer": [
        "frontend", "front end", "react", "react.js", "javascript",
        "html", "css", "tailwind", "bootstrap", "responsive design",
        "ui development", "web interface", "component", "user interface"
    ],

    "Backend Developer": [
        "backend", "back end", "node", "node.js", "express",
        "spring boot", "rest api", "rest apis", "api development",
        "server", "server side", "mongodb", "mysql", "database",
        "authentication", "admin dashboard"
    ],

    "Full Stack Developer": [
        "full stack", "full-stack", "mern", "react", "node",
        "node.js", "express", "mongodb", "frontend", "backend",
        "rest api", "rest apis", "web application", "crud"
    ],

    "QA Engineer": [
        "qa", "quality assurance", "software testing", "manual testing",
        "automation testing", "selenium", "postman", "jira",
        "test cases", "test case", "bug reporting", "test plan",
        "defect", "quality"
    ],

    "Data Analyst": [
        "data analyst", "data analysis", "analytics", "python",
        "sql", "mysql", "excel", "power bi", "dashboard",
        "reporting", "data cleaning", "visualization", "statistics",
        "business intelligence"
    ],

    "UI UX Designer": [
        "ui ux", "ui/ux", "ux designer", "ui designer", "figma",
        "wireframe", "wireframes", "prototype", "prototyping",
        "user research", "usability testing", "user interface",
        "user experience", "design system"
    ],

    "Cloud Engineer": [
        "cloud", "cloud engineer", "aws", "azure", "google cloud",
        "linux", "docker", "terraform", "networking", "cloud computing",
        "ec2", "s3", "iam", "deployment"
    ],

    "DevOps Engineer": [
        "devops", "ci cd", "ci/cd", "docker", "kubernetes",
        "jenkins", "linux", "aws", "deployment", "pipeline",
        "terraform", "automation", "monitoring"
    ],

    "Business Analyst": [
        "business analyst", "requirements", "requirement gathering",
        "user stories", "documentation", "process modelling",
        "process modeling", "stakeholder", "business process",
        "analysis", "functional requirement", "non functional requirement"
    ],

    "Cyber Security Analyst": [
        "cyber security", "cybersecurity", "network security",
        "security analyst", "ethical hacking", "vulnerability",
        "penetration testing", "firewall", "threat", "risk",
        "security monitoring"
    ],

    "Machine Learning Engineer": [
        "machine learning", "deep learning", "nlp", "ai",
        "artificial intelligence", "model training", "classification",
        "regression", "tensorflow", "pytorch", "scikit-learn",
        "data science"
    ]
}


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z0-9\s+#./-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_keyword_matches(text, keywords):
    matched_keywords = []

    for keyword in keywords:
        keyword_clean = keyword.lower().strip()

        if keyword_clean in text:
            matched_keywords.append(keyword)

    return matched_keywords


def build_label_text(row):
    combined_text = f"""
    {row.get("skills", "")}
    {row.get("projects", "")}
    {row.get("tools", "")}
    {row.get("experience", "")}
    {row.get("certifications", "")}
    {row.get("education", "")}
    {row.get("cv_text", "")}
    """

    return clean_text(combined_text)


def suggest_label(row):
    text = build_label_text(row)

    role_results = {}

    for role, keywords in ROLE_KEYWORDS.items():
        matched_keywords = count_keyword_matches(text, keywords)

        role_results[role] = {
            "matched_keywords": matched_keywords,
            "match_count": len(matched_keywords)
        }

    sorted_roles = sorted(
        role_results.items(),
        key=lambda item: item[1]["match_count"],
        reverse=True
    )

    best_role = sorted_roles[0][0]
    best_keywords = sorted_roles[0][1]["matched_keywords"]
    best_count = sorted_roles[0][1]["match_count"]

    second_best_role = sorted_roles[1][0] if len(sorted_roles) > 1 else ""

    if best_count == 0:
        best_role = "Software Engineer"
        review_note = "No clear role-specific keywords found. Please review this label manually."
    elif best_count <= 2:
        review_note = "Limited role-specific keywords found. Please review this label manually."
    else:
        review_note = "Suggested label based on matched CV skills, tools, projects, education, experience, and certifications."

    return {
        "career_path_label": best_role,
        "second_best_role": second_best_role,
        "matched_keywords": ", ".join(best_keywords),
        "review_note": review_note
    }


def main():
    print("===================================")
    print("AUTO CV LABELLING STARTED")
    print("===================================")

    if not os.path.exists(INPUT_FILE):
        print("cv_extracted_text.csv not found.")
        print("Run extract_cv_sections.py first.")
        return

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "file_name", "cv_text", "skills", "projects", "education",
        "tools", "experience", "certifications"
    ]

    for column in required_columns:
        if column not in df.columns:
            df[column] = ""

    records = []

    for _, row in df.iterrows():
        suggestion = suggest_label(row)

        records.append({
            "file_name": str(row["file_name"]).strip(),
            "career_path_label": suggestion["career_path_label"],
            "second_best_role": suggestion["second_best_role"],
            "matched_keywords": suggestion["matched_keywords"],
            "review_note": suggestion["review_note"]
        })

    output_df = pd.DataFrame(records)

    output_df.to_csv(AUTO_LABEL_FILE, index=False, encoding="utf-8")

    final_df = output_df[["file_name", "career_path_label"]]
    final_df.to_csv(FINAL_LABEL_FILE, index=False, encoding="utf-8")

    print("\n===================================")
    print("AUTO CV LABELLING COMPLETED")
    print("===================================")
    print("Total CVs labelled:", len(output_df))
    print("Auto label file saved:", AUTO_LABEL_FILE)
    print("Final label file saved:", FINAL_LABEL_FILE)

    print("\nLabel distribution:")
    print(output_df["career_path_label"].value_counts())

    print("\nNext step:")
    print("Open cv_labels_auto.csv and review labels.")
    print("If needed, correct cv_labels.csv before training.")


if __name__ == "__main__":
    main()