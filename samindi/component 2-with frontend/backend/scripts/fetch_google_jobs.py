import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, ".env")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "job_posts.csv")

load_dotenv(ENV_FILE)

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

SEARCH_ROLES = [
    "Software Engineer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "QA Engineer",
    "Data Analyst",
    "UI UX Designer",
    "Cloud Engineer",
    "DevOps Engineer",
    "Business Analyst"
]

LOCATION = "Sri Lanka"
RESULTS_PER_ROLE = 10


def clean_text(text):
    return " ".join(str(text).replace("\n", " ").replace("\r", " ").split())


def fetch_google_jobs(role):
    if not SERPAPI_KEY:
        raise ValueError("SERPAPI_KEY not found in backend/.env")

    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_jobs",
        "q": role,
        "location": LOCATION,
        "api_key": SERPAPI_KEY
    }

    response = requests.get(url, params=params, timeout=40)
    response.raise_for_status()

    data = response.json()
    jobs = data.get("jobs_results", [])

    records = []

    for index, job in enumerate(jobs[:RESULTS_PER_ROLE], start=1):
        title = clean_text(job.get("title", ""))
        company = clean_text(job.get("company_name", ""))
        location = clean_text(job.get("location", ""))
        description = clean_text(job.get("description", ""))

        apply_links = job.get("apply_options", [])
        source_url = ""

        if apply_links:
            source_url = apply_links[0].get("link", "")

        detected_extensions = job.get("detected_extensions", {})
        posted_at = detected_extensions.get("posted_at", "")

        records.append({
            "job_id": f"{role.replace(' ', '_').lower()}_{index}",
            "job_title": title,
            "job_role": role,
            "company": company,
            "location": location,
            "job_description": description,
            "required_skills": description,
            "source_url": source_url,
            "posted_at": posted_at,
            "data_source": "Google Jobs via SerpAPI"
        })

    return records


def main():
    all_records = []

    for role in SEARCH_ROLES:
        print("Searching Google Jobs for:", role)

        try:
            role_records = fetch_google_jobs(role)
            all_records.extend(role_records)
            print("Jobs collected:", len(role_records))

        except Exception as error:
            print("Failed for role:", role)
            print("Error:", error)

        time.sleep(2)

    if not all_records:
        print("No jobs collected. Please check SERPAPI_KEY or internet connection.")
        return

    df = pd.DataFrame(all_records)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("\n===================================")
    print("GOOGLE JOB POSTS SAVED")
    print("===================================")
    print("Total job posts:", len(df))
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()