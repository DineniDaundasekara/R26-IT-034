from fastapi import FastAPI, UploadFile, Form, File
from data_extraction import extract_github_metrics, extract_pdf_features
from explainability import explain_decision
import json

app = FastAPI()

@app.post("/analyze_candidate")
async def analyze_candidate(
    github_username: str = Form(...),
    resume: UploadFile = File(...)
):
    pdf_bytes = await resume.read()
    
    pdf_features = extract_pdf_features(pdf_bytes)
    github_features = extract_github_metrics(github_username)
    
    sample_vector = [
        github_features.get("github_followers", 0),
        github_features.get("github_public_repos", 0),
        pdf_features.get("years_of_experience", 0),
        pdf_features.get("skill_match_count", 0),
        github_features.get("commit_frequency", 0),
        github_features.get("repo_quality_score", 0),
        github_features.get("collaboration_score", 0)
    ]
    
    results = explain_decision("hiring_model.pkl", "feature_names.json", sample_vector)
    
    return {
        "success": True,
        "candidate": {
            "github_username": github_username,
            "github_followers": github_features.get("github_followers", 0),
            "github_public_repos": github_features.get("github_public_repos", 0),
            "commit_frequency": github_features.get("commit_frequency", 0),
            "repo_quality_score": github_features.get("repo_quality_score", 0),
            "collaboration_score": github_features.get("collaboration_score", 0),
            "open_source_contributions": github_features.get("open_source_contributions", 0),
            "preferred_languages": github_features.get("preferred_languages", []),
            "years_of_experience": pdf_features.get("years_of_experience", 0),
            "matched_skills": pdf_features.get("matched_skills", [])
        },
        "trust_score": results["trust_score"],
        "risk_category": results["risk_category"],
        "explanations": results["explanations"]
    }
