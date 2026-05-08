import requests
import os

import PyPDF2
import spacy
import re
from io import BytesIO

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # For demonstration without forcing download, we fallback if not downloaded.
    nlp = None

def extract_github_metrics(username: str):
    """
    Given a Github username, fetch detailed metrics from multiple endpoints.
    """
    headers = {"User-Agent": "AI-Hiring-System"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    # 1. Basic User Info
    user_url = f"https://api.github.com/users/{username}"
    user_resp = requests.get(user_url, headers=headers)
    
    if user_resp.status_code != 200:
        return {
            "github_followers": 0,
            "github_public_repos": 0,
            "commit_frequency": 0,
            "repo_quality_score": 0,
            "collaboration_score": 0,
            "open_source_contributions": 0,
            "preferred_languages": []
        }
    
    user_data = user_resp.json()
    followers = user_data.get("followers", 0)
    public_repos = user_data.get("public_repos", 0)

    # 2. Repository Analysis (Quality & Languages)
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    repos_resp = requests.get(repos_url, headers=headers)
    
    repo_quality_score = 0
    languages = {}
    
    if repos_resp.status_code == 200:
        repos_data = repos_resp.json()
        total_stars = sum([r.get("stargazers_count", 0) for r in repos_data])
        total_forks = sum([r.get("forks_count", 0) for r in repos_data])
        
        # Calculate a quality score based on stars and forks per repo
        if len(repos_data) > 0:
            repo_quality_score = min(10, (total_stars * 2 + total_forks) / len(repos_data))
        
        for r in repos_data:
            lang = r.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
    
    # Sort languages by frequency
    preferred_languages = sorted(languages.keys(), key=lambda x: languages[x], reverse=True)[:3]

    # 3. Activity & Collaboration Analysis (from Events)
    events_url = f"https://api.github.com/users/{username}/events?per_page=100"
    events_resp = requests.get(events_url, headers=headers)
    
    commit_frequency = 0
    collaboration_score = 0
    open_source_contributions = 0
    
    if events_resp.status_code == 200:
        events_data = events_resp.json()
        
        # Count different types of events
        push_events = [e for e in events_data if e["type"] == "PushEvent"]
        pr_events = [e for e in events_data if e["type"] in ["PullRequestEvent", "PullRequestReviewEvent"]]
        issue_events = [e for e in events_data if e["type"] == "IssueCommentEvent"]
        
        # Simple commit frequency (pushes in the last 100 events)
        commit_frequency = min(10, len(push_events) / 5)
        
        # Collaboration score (PRs and Issues)
        collaboration_score = min(10, (len(pr_events) * 2 + len(issue_events)) / 2)
        
        # Open source contributions (events on repos not owned by user)
        os_events = [e for e in events_data if not e["repo"]["name"].startswith(f"{username}/")]
        open_source_contributions = min(10, len(os_events) / 3)

    return {
        "github_followers": followers,
        "github_public_repos": public_repos,
        "commit_frequency": round(commit_frequency, 2),
        "repo_quality_score": round(repo_quality_score, 2),
        "collaboration_score": round(collaboration_score, 2),
        "open_source_contributions": round(open_source_contributions, 2),
        "preferred_languages": preferred_languages
    }

def extract_pdf_features(pdf_bytes: bytes):
    """
    Given a PDF file stream, extract raw text and basic features.
    """
    try:
        reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    except Exception:
        text = ""
        
    text_lower = text.lower()
    
    # Very basic skills matching
    predefined_skills = ["python", "javascript", "react", "node", "sql", "machine learning", "docker", "aws", "kubernetes", "fastapi", "express", "mongodb", "java", "c++"]
    matched_skills = list(set([skill for skill in predefined_skills if skill in text_lower]))
    skill_match_count = len(matched_skills)
    
    # Very basic experience extraction regex looking for "X years experience"
    exp_matches = re.findall(r'(\d+)\+?\s*years?', text_lower)
    years_of_experience = 0
    if exp_matches:
        years_of_experience = max([int(m) for m in exp_matches])
    
    return {
        "years_of_experience": years_of_experience,
        "skill_match_count": skill_match_count,
        "matched_skills": matched_skills
    }
