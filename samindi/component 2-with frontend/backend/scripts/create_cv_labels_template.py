import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CV_FOLDER = os.path.join(BASE_DIR, "data", "cvs")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "cv_labels.csv")

career_labels = [
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

records = []

for file_name in os.listdir(CV_FOLDER):
    if file_name.lower().endswith(".pdf"):
        records.append({
            "file_name": file_name,
            "career_path_label": ""
        })

df = pd.DataFrame(records)
df = df.sort_values("file_name")

df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

print("CV label template created successfully.")
print("Saved:", OUTPUT_FILE)
print("Total PDF files found:", len(df))
print("\nNow open cv_labels.csv and fill career_path_label for each CV.")
print("\nAllowed example labels:")
for label in career_labels:
    print("-", label)