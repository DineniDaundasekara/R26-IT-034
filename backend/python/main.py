"""
FastAPI Application Entry Point (Port 8000)
======================================================
High-performance AI candidate assessment microservice with ESCO v1.1
knowledge graph, multi-format PDF claim parsing, GitHub artifact mining,
temporal calibration, 4-way epistemic NLI, and supervised ML inference.
"""

import os
import sys
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Add python microservice directory and workspace root to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.abspath(os.path.join(backend_dir, "..", ".."))

load_dotenv(os.path.join(backend_dir, ".env"), override=True)
load_dotenv(os.path.join(workspace_root, ".env"), override=True)

for p in [backend_dir, workspace_root]:
    if p not in sys.path:
        sys.path.insert(0, p)


from hr_ml.esco_ontology import get_esco_ontology
from hr_ml.resume_parser import ResumeDocumentParser, ResumeClaimExtractor
from hr_ml.github_miner import GitHubEvidenceMiner
from hr_ml.temporal_calibrator import TemporalCalibrator
from hr_ml.claim_verifier import CrossSourceClaimVerifier
from hr_ml.model_service import get_ml_model_service
from hr_ml.guidance import RecruiterGuidanceEngine
from hr_ml.labels import get_label_info, CLASSES
from hr_ml.linkedin_retriever import get_linkedin_retriever


# Initialize FastAPI App
app = FastAPI(
    title="Technical Candidate Assessment & Consistency Verification Engine",
    description="Evidence-based decision-support system for technical recruitment with 4-way Epistemic NLI and Supervised ML.",
    version="1.0.0"
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core AI Verification Pipelines
esco = get_esco_ontology()
resume_extractor = ResumeClaimExtractor(esco)
github_miner = GitHubEvidenceMiner()
temporal_calibrator = TemporalCalibrator()
verifier = CrossSourceClaimVerifier(
    esco=esco,
    resume_extractor=resume_extractor,
    github_miner=github_miner,
    temporal_calibrator=temporal_calibrator
)
ml_service = get_ml_model_service()
linkedin_retriever = get_linkedin_retriever()

# Local data persistence store (JSON fallback)

DB_FILE = os.path.join(backend_dir, "data_store.json")


def load_db() -> Dict[str, Any]:
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"candidates": {}, "custom_roles": {}}


def save_db(data: Dict[str, Any]):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Warning] Failed to save data store: {e}")


# Pydantic Request Models
class DecisionRequest(BaseModel):
    decision: str
    notes: Optional[str] = ""
    reviewerName: Optional[str] = "Hiring Manager"


class RoleConfigModel(BaseModel):
    roleId: str
    roleName: str
    category: str
    requiredSkills: List[Dict[str, Any]]
    preferredSkills: List[Dict[str, Any]]


# ==============================================================================
# API Endpoints
# ==============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint providing pipeline and ontology status."""
    return {
        "status": "healthy",
        "service": "Candidate Assessment Python AI Microservice",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "esco_skills_loaded": len(getattr(esco, "skills_by_uri", getattr(esco, "skills", []))),
        "esco_occupations_loaded": len(getattr(esco, "occupations_by_uri", {})),
        "ml_model_loaded": ml_service.is_loaded,
        "ml_model_name": ml_service.model_name
    }


@app.get("/api/roles")
def get_roles():
    """Returns available standard ESCO and custom-configured job role definitions."""
    db = load_db()
    standard_roles = [
        esco.get_default_role_config("full stack mern developer"),
        esco.get_default_role_config("backend python engineer"),
        esco.get_default_role_config("frontend react developer"),
        esco.get_default_role_config("devops engineer"),
        esco.get_default_role_config("data scientist")
    ]
    custom_roles = list(db.get("custom_roles", {}).values())
    return {
        "standardRoles": standard_roles,
        "customRoles": custom_roles,
        "roles": standard_roles + custom_roles
    }


@app.post("/api/roles")
def create_custom_role(role: RoleConfigModel):
    """Saves a custom recruiter-configured job role profile."""
    db = load_db()
    db["custom_roles"][role.roleId] = role.dict()
    save_db(db)
    return {"status": "SUCCESS", "role": role.dict()}


@app.get("/api/skills/search")
def search_skills(q: str):
    """Searches ESCO skills and tech dictionary for dynamic configuration."""
    canonical = esco.resolve_canonical_skill_name(q)
    skill_meta = esco.lookup_skill(q)
    return {
        "query": q,
        "canonical": canonical,
        "metadata": skill_meta
    }


@app.post("/api/assess/candidate")
@app.post("/api/candidates/assess")
async def assess_candidate(

    candidate_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    github_username: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    apify_token: Optional[str] = Form(None),
    target_role: Optional[str] = Form(None),
    target_role_id: Optional[str] = Form("full_stack_mern"),
    resume_text: Optional[str] = Form(None),
    resume_file: Optional[UploadFile] = File(None),
    resume: Optional[UploadFile] = File(None)
):
    """
    Main candidate assessment endpoint. Ingests PDF or text, extracts claims,
    mines GitHub repositories and package manifests, computes temporal calibration,
    retrieves direct LinkedIn profile and certification data, and produces an
    explainable, evidence-backed assessment report.
    """
    uploaded_file = resume_file or resume
    extracted_text = ""
    filename = "pasted_text.txt"

    if uploaded_file and uploaded_file.filename:
        content_bytes = await uploaded_file.read()
        filename = uploaded_file.filename
        extracted_text = ResumeDocumentParser.extract_text(content_bytes, filename)
    elif resume_text:
        extracted_text = resume_text
    else:
        raise HTTPException(
            status_code=400,
            detail="Either a resume PDF upload (resume_file) or resume_text must be provided."
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text could be extracted from the uploaded document."
        )

    # Resolve target role configuration
    db = load_db()
    resolved_role_key = target_role or target_role_id or "full_stack_mern"
    role_config = None
    if resolved_role_key in db.get("custom_roles", {}):
        role_config = db["custom_roles"][resolved_role_key]
    else:
        role_config = esco.get_default_role_config(resolved_role_key)

    # Clean and resolve candidate handles
    clean_github = GitHubEvidenceMiner.clean_username(github_username)

    # Run verification pipeline
    assessment_result = verifier.verify_candidate(
        resume_text=extracted_text,
        target_role_config=role_config,
        github_username=clean_github or None,
        candidate_name=candidate_name
    )

    # Retrieve direct LinkedIn profile details (profile pic, current role, certifications)
    # Note: No ontology mapping or cross-source penalties applied as per research constraints
    active_token = (apify_token.strip() if apify_token and apify_token.strip() else None) or os.getenv("APIFY_API_TOKEN")
    linkedin_data = linkedin_retriever.get_profile_data(
        linkedin_url=linkedin_url,
        candidate_name=candidate_name or assessment_result.get("candidateName"),
        github_username=assessment_result.get("githubUsername") or clean_github,
        resume_text=extracted_text,
        api_token=active_token
    )
    assessment_result["linkedinData"] = linkedin_data

    # Generate tailored interview probes
    interview_probes = RecruiterGuidanceEngine.generate_interview_probes(
        assessment_result.get("skillVerifications", [])
    )
    assessment_result["interviewProbes"] = interview_probes

    assessment_id = str(uuid.uuid4())
    assessment_record = {
        "assessmentId": assessment_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "candidateName": candidate_name or assessment_result.get("candidateName", "Candidate"),
        "email": email or assessment_result.get("contact", {}).get("email"),
        "githubUsername": assessment_result.get("githubUsername") or clean_github,
        "linkedinUrl": linkedin_url or linkedin_data.get("linkedin_url"),
        "linkedinProfile": linkedin_data,
        "linkedinData": linkedin_data,
        "targetRole": role_config.get("roleName", "Full Stack MERN Developer"),
        "targetRoleId": resolved_role_key,
        "assessment": assessment_result,
        "hrDecision": None
    }

    # Persist in local data store
    db["candidates"][assessment_id] = assessment_record
    save_db(db)

    return assessment_record



@app.get("/api/candidates")
def get_candidates():
    """Returns list of assessed candidates sorted by date."""
    db = load_db()
    items = list(db.get("candidates", {}).values())
    items.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
    return items


@app.get("/api/candidates/{assessment_id}")
def get_candidate_detail(assessment_id: str):
    """Returns detailed assessment record for a specific candidate."""
    db = load_db()
    if assessment_id not in db.get("candidates", {}):
        raise HTTPException(status_code=404, detail="Candidate assessment record not found.")
    return db["candidates"][assessment_id]


@app.post("/api/candidates/{assessment_id}/decision")
def record_hr_decision(assessment_id: str, decision: DecisionRequest):
    """Records human-in-the-loop recruiter decision and notes."""
    db = load_db()
    if assessment_id not in db.get("candidates", {}):
        raise HTTPException(status_code=404, detail="Candidate assessment record not found.")

    db["candidates"][assessment_id]["hrDecision"] = {
        "decision": decision.decision,
        "notes": decision.notes,
        "reviewerName": decision.reviewerName,
        "decidedAt": datetime.now(timezone.utc).isoformat()
    }
    save_db(db)
    return {"status": "SUCCESS", "record": db["candidates"][assessment_id]}


@app.delete("/api/candidates/{assessment_id}")
def delete_candidate(assessment_id: str):
    """Deletes an assessment record for a candidate by assessmentId."""
    db = load_db()
    candidates = db.get("candidates", {})
    if assessment_id in candidates:
        del candidates[assessment_id]
        save_db(db)
        return {"status": "SUCCESS", "message": f"Candidate {assessment_id} deleted successfully."}
    
    # Also check if any candidate matches by _id or nested assessmentId
    for k, v in list(candidates.items()):
        if str(v.get("assessmentId")) == assessment_id or str(v.get("_id")) == assessment_id or str(k) == assessment_id:
            del candidates[k]
            save_db(db)
            return {"status": "SUCCESS", "message": f"Candidate {assessment_id} deleted successfully."}

    raise HTTPException(status_code=404, detail="Candidate assessment record not found.")


@app.get("/api/ablation")
@app.get("/api/experiments/ablation")
def get_ablation_results():
    """Returns the empirical ablation study results (Model A vs Model B vs Model C)."""
    candidate_paths = [
        os.path.join(backend_dir, "models", "ablation_study_results.json"),
        os.path.join(workspace_root, "results", "ablation_study_results.json")
    ]
    for results_path in candidate_paths:
        if os.path.exists(results_path):
            try:
                with open(results_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to read ablation results: {e}")
    return {"status": "NOT_FOUND", "message": "Run ablation experiments first."}


# Mount Frontend Distribution if available
frontend_dist = os.path.join(workspace_root, "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")


@app.get("/")
def serve_root():
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "service": "Candidate Assessment AI Microservice",
        "status": "RUNNING",
        "docs": "/docs",
        "health": "/health"
    }


def start_server(port: int = 8000, host: str = "127.0.0.1"):
    """Launches the Uvicorn server."""
    import uvicorn
    print(f"[FastAPI] Starting server on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    start_server(port=port, host=host)
