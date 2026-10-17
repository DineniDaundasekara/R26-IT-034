import os
import sys
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .auth import (
    AuthLoginRequest,
    AuthRegisterRequest,
    authenticate_token,
    init_auth_db,
    login_user,
    logout_session,
    mongo_ready,
    register_user,
    require_admin,
)

# Setup Base Paths
APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
SAM_DIR = ROOT_DIR / "samindi"
IR_BACKEND_DIR = SAM_DIR / "InterviewReady" / "nlp-component" / "backend"
C2_BACKEND_DIR = SAM_DIR / "component 2-with frontend" / "backend"
CR_BACKEND_DIR = SAM_DIR / "CareerRisk" / "backend"
EMP_BACKEND_DIR = SAM_DIR / "Employability" / "backend"
HR_BACKEND_DIR = SAM_DIR / "HRCandidateSelection" / "backend"
STATIC_DIR = APP_DIR / "static"

# Load environment variables across possible .env locations
# Employability keeps its key in samindi/Employability/.env (parent of backend/)
EMP_DIR = EMP_BACKEND_DIR.parent
for env_file in [
    ROOT_DIR / ".env",
    IR_BACKEND_DIR / ".env",
    C2_BACKEND_DIR / ".env",
    CR_BACKEND_DIR / ".env",
    EMP_DIR / ".env",
    EMP_BACKEND_DIR / ".env",
    HR_BACKEND_DIR / ".env",
]:
    if env_file.exists():
        load_dotenv(env_file, override=True)

# Ensure backend directories are included in sys.path
for p in [str(ROOT_DIR), str(IR_BACKEND_DIR), str(C2_BACKEND_DIR), str(CR_BACKEND_DIR), str(EMP_BACKEND_DIR), str(HR_BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Import InterviewReady ML & Service modules
from ml.ai_guidance import generate_ai_guidance, generate_follow_up
from ml.config import (
    AUDIO_EXTENSIONS,
    MODEL_FILE as IR_MODEL_FILE,
    OPENAI_API_KEY,
    OPENAI_GUIDANCE_ENABLED,
    OPENAI_GUIDANCE_MODEL,
    OPENAI_GUIDANCE_VERIFY,
    OPENAI_VERIFIER_MODEL,
    TEMP_DIR,
)
from ml.guidance import build_advanced_fallback, build_follow_up_fallback, build_guidance
from ml.model_service import predict_communication_level
from ml.transcriber import transcribe_audio

# Import CareerLens Services
from services.career_path_model_service import CareerPathModelService
from services.cv_reader import build_cv_evidence, extract_cv_text
from services.guidance_service import GuidanceService
from services.job_match_service import compare_cv_to_jobs
from services.job_search_service import JobSearchService
from services.readiness_service import ReadinessService

# Import CareerRisk (Career Safety & Industry Stability Analysis) Service
from career_risk_engine import CareerRiskService
import history_store as career_risk_history

# Import Employability Simulator (Internship / Competence / PsyCap → Employability) Service
from employability_service import build_phase_services

# Import HR Candidate Selection (admin-only cross-source candidate verification) Service
from hr_candidate_service import HRCandidateService

# Initialize FastAPI App
app = FastAPI(
    title="Career Intelligence Platform - Comprehensive Career Development and Recruitment Framework",
    version="4.0.0",
    description=(
        "Unified Research Platform: spoken audio NLP communication classification with grounded "
        "AI interview coaching; supervised CV career-path classification with decoupled readiness "
        "evaluation and real-time job market matching; explainable Random Forest career risk & "
        "industry stability analysis; behaviour-aware employability simulation; and an admin-only "
        "HR candidate selection tool cross-referencing resume claims against GitHub and LinkedIn "
        "evidence for human-in-the-loop hiring decisions."
    ),
)

# Enable CORS for development and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MongoDB authentication (users + sessions)
try:
    init_auth_db()
except Exception as exc:
    print(f"[INIT WARNING] MongoDB auth not ready: {exc}")

# Initialize CV Career Path Model
career_model = CareerPathModelService(C2_BACKEND_DIR)
try:
    career_model.load()
    print("[INIT] Career path ML model loaded successfully.")
except Exception as exc:
    print(f"[INIT WARNING] Career path model not pre-loaded: {exc}")

readiness_service = ReadinessService()

# Initialize Career Risk Model (Career Safety & Industry Stability Analysis)
career_risk_service = CareerRiskService(CR_BACKEND_DIR)
try:
    career_risk_service.load()
    print("[INIT] Career risk model loaded successfully.")
except Exception as exc:
    print(f"[INIT WARNING] Career risk model not pre-loaded: {exc}")

try:
    career_risk_history.init_db()
except Exception as exc:
    print(f"[INIT WARNING] Career risk history database init warning: {exc}")

# Initialize Employability Simulator Services (Phase 1/2/3 frozen models)
employability_services = build_phase_services(EMP_BACKEND_DIR)
for _phase_id, _phase_service in employability_services.items():
    try:
        _phase_service.load()
        print(f"[INIT] Employability {_phase_id} model loaded successfully.")
    except Exception as exc:
        print(f"[INIT WARNING] Employability {_phase_id} model not pre-loaded: {exc}")

# Initialize HR Candidate Selection Service (admin-only)
hr_candidate_service = HRCandidateService(HR_BACKEND_DIR)
try:
    hr_candidate_service.load()
    print("[INIT] HR Candidate Selection ESCO ontology & ML model loaded successfully.")
except Exception as exc:
    print(f"[INIT WARNING] HR Candidate Selection service not pre-loaded: {exc}")


# ============================================================================
# AUTHENTICATION (LOGIN / REGISTER)
# ============================================================================

@app.post("/api/auth/register")
def auth_register(payload: AuthRegisterRequest):
    return register_user(payload)


@app.post("/api/auth/login")
def auth_login(payload: AuthLoginRequest):
    return login_user(payload)


@app.get("/api/auth/me")
def auth_me(authorization: Optional[str] = Header(default=None)):
    return authenticate_token(authorization)


@app.post("/api/auth/logout")
def auth_logout(authorization: Optional[str] = Header(default=None)):
    return logout_session(authorization)


# ============================================================================
# HEALTH & METADATA ENDPOINTS
# ============================================================================

@app.get("/api/health")
@app.get("/health")
def health_status():
    job_service = JobSearchService()
    cv_guidance = GuidanceService()

    return {
        "status": "ok",
        "success": True,
        "communicationModelReady": IR_MODEL_FILE.exists(),
        "careerModelReady": career_model.exists(),
        "careerRiskModelReady": career_risk_service.exists(),
        "employabilityModelsReady": all(s.exists() for s in employability_services.values()),
        "hrCandidateModelReady": hr_candidate_service.exists(),
        "serpapiConfigured": job_service.configured(),
        "groqConfigured": cv_guidance.configured(),
        "mongoAuthReady": mongo_ready(),
        "openaiGuidanceReady": bool(OPENAI_GUIDANCE_ENABLED and OPENAI_API_KEY),
        "aiGuidanceModel": (
            OPENAI_GUIDANCE_MODEL
            if OPENAI_GUIDANCE_ENABLED and OPENAI_API_KEY
            else None
        ),
        "aiGuidanceVerification": bool(
            OPENAI_GUIDANCE_ENABLED and OPENAI_API_KEY and OPENAI_GUIDANCE_VERIFY
        ),
        "aiVerifierModel": (
            OPENAI_VERIFIER_MODEL
            if OPENAI_GUIDANCE_ENABLED and OPENAI_API_KEY and OPENAI_GUIDANCE_VERIFY
            else None
        ),
    }


@app.get("/api/modules")
def list_modules():
    return {
        "success": True,
        "modules": [
            {
                "id": "communication",
                "title": "Interview Readiness & Communication Guidance",
                "subtitle": "InterviewReady",
                "badge": "NLP + Spoken Audio ML",
                "description": (
                    "Practice spoken interview answers with live recording or audio upload, "
                    "get ML-predicted communication level, acoustic diagnostics, STAR framework analysis, "
                    "and grounded AI coaching."
                ),
                "route": "/communication-guidance",
                "features": [
                    "Faster-Whisper Speech Recognition",
                    "Acoustic & NLP Feature Extraction",
                    "Supervised ML Communication Classifier",
                    "Grounded AI Coaching & STAR Framework",
                ],
            },
            {
                "id": "career",
                "title": "CV based career path guidance",
                "subtitle": "CareerLens",
                "badge": "Supervised CV Classifier & Market Matching",
                "description": (
                    "Upload a CV in PDF/DOCX/TXT format, classify career direction with trained ML, "
                    "evaluate decoupled structural quality vs market alignment, and discover live vacancies."
                ),
                "route": "/cv-guidance",
                "features": [
                    "Automated CV Text & Evidence Extraction",
                    "TF-IDF + ML Career Path Classifier",
                    "Decoupled 2D CV Evaluation Matrix",
                    "Google Jobs, TopJobs & LinkedIn Matching",
                ],
            },
            {
                "id": "career-risk",
                "title": "Career Safety & Industry Stability",
                "subtitle": "Career Safety AI",
                "badge": "Random Forest + Grounded AI Guidance",
                "description": (
                    "Answer a short career profile questionnaire to get an explainable "
                    "overall career risk level, system-derived stability indicators, and "
                    "a personalized 30/60/90-day AI career resilience action plan."
                ),
                "route": "/career-risk-guidance",
                "features": [
                    "Supervised Random Forest Risk Classifier",
                    "Auxiliary Indicator Sub-Models",
                    "Explainable Risk Factor Mapping",
                    "30/60/90-Day AI Resilience Action Plan",
                ],
            },
            {
                "id": "employability",
                "title": "Employability Simulator",
                "subtitle": "Behaviour-Aware Career Simulation",
                "badge": "3 Validated Regression Models",
                "description": (
                    "Complete a short internship experience, competence, or psychological "
                    "capital assessment to generate an explainable employability prediction "
                    "with construct-level breakdowns and personalized development guidance."
                ),
                "route": "/employability-simulation",
                "features": [
                    "Phase 1: Internship Experience (XGBoost)",
                    "Phase 2: Competence (Linear Regression)",
                    "Phase 3: Psychological Capital (ElasticNet)",
                    "Construct-Level Strengths & Development Priorities",
                ],
            },
            {
                "id": "hr-candidates",
                "title": "HR Candidate Selection",
                "subtitle": "Admin-Only Cross-Source Candidate Verification",
                "badge": "GitHub + LinkedIn Evidence & 4-Way Epistemic NLI",
                "description": (
                    "Admin-only recruiter tool: cross-references a candidate resume against "
                    "independent public GitHub artifacts and a direct LinkedIn profile lookup, "
                    "producing an explainable, evidence-grounded assessment with a "
                    "human-in-the-loop hiring decision panel."
                ),
                "route": "/hr-candidate-selection",
                "adminOnly": True,
                "features": [
                    "ESCO v1.1 Knowledge Graph",
                    "GitHub Evidence Mining",
                    "Direct LinkedIn Profile Lookup",
                    "4-Way Epistemic Claim Verification",
                    "Recruiter Decision Support",
                ],
            },
        ],
    }


# ============================================================================
# COMPONENT 1: INTERVIEWREADY (COMMUNICATION SKILL GUIDANCE)
# ============================================================================

class CoachFollowUpRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=12000)
    communicationLevel: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=1, max_length=1000)
    targetRole: str = Field(default="", max_length=120)


@app.post("/api/coach/follow-up")
def coach_follow_up(payload: CoachFollowUpRequest):
    fallback_answer = build_follow_up_fallback(
        transcript=payload.transcript,
        communication_level=payload.communicationLevel,
        question=payload.question,
        target_role=payload.targetRole,
    )

    if not (OPENAI_GUIDANCE_ENABLED and OPENAI_API_KEY):
        return {
            "success": True,
            "fallback": True,
            "mode": "local-evidence-coach",
            "message": "Using the built-in evidence-based coach because generative AI key is not configured.",
            "answer": fallback_answer,
        }

    try:
        answer = generate_follow_up(
            transcript=payload.transcript,
            communication_level=payload.communicationLevel,
            question=payload.question,
            target_role=payload.targetRole,
        )
        if not answer:
            raise RuntimeError("No coach response was generated.")

        return {
            "success": True,
            "fallback": False,
            "mode": "openai-grounded",
            "message": "",
            "answer": answer,
        }
    except Exception as error:
        print(f"AI coach provider error; using fallback: {type(error).__name__}")
        return {
            "success": True,
            "fallback": True,
            "mode": "local-evidence-coach",
            "message": "AI Coach is using the built-in evidence-based mode.",
            "answer": fallback_answer,
        }


@app.post("/api/analyze/audio")
async def analyze_audio(
    audio: UploadFile = File(...),
    target_role: str = Form(default=""),
    experience_level: str = Form(default=""),
    practice_goal: str = Form(default=""),
):
    original_name = audio.filename or "recording.webm"
    suffix = Path(original_name).suffix.lower()

    if suffix not in AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format. Use WAV, MP3, M4A, OGG, WEBM, FLAC, or AAC.",
        )

    temp_path = TEMP_DIR / f"{uuid.uuid4().hex}{suffix}"

    try:
        with temp_path.open("wb") as output:
            shutil.copyfileobj(audio.file, output)

        if temp_path.stat().st_size == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded audio file is empty.",
            )

        transcript = transcribe_audio(str(temp_path))

        if not transcript:
            raise HTTPException(
                status_code=422,
                detail="Whisper could not detect usable speech in this recording. Please speak clearly into the microphone.",
            )

        communication_level = predict_communication_level(
            transcript,
            str(temp_path),
        )

        baseline = build_guidance(
            transcript,
            communication_level,
            audio_path=str(temp_path),
        )

        guidance_mode = "evidence-fallback"
        ai_error = None
        advanced = None

        try:
            advanced = generate_ai_guidance(
                transcript=transcript,
                communication_level=communication_level,
                evidence=baseline["evidence"],
                deterministic_guidance=baseline,
                target_role=target_role.strip(),
                experience_level=experience_level.strip(),
                practice_goal=practice_goal.strip(),
            )
            if advanced:
                guidance_mode = (
                    "openai-grounded-verified"
                    if OPENAI_GUIDANCE_VERIFY
                    else "openai-grounded"
                )
        except Exception as error:
            ai_error = str(error)

        if advanced is None:
            advanced = build_advanced_fallback(
                transcript=transcript,
                communication_level=communication_level,
                baseline=baseline,
                target_role=target_role.strip(),
            )

        return {
            "success": True,
            "data": {
                "transcript": transcript,
                "communicationLevel": communication_level,
                "guidanceMode": guidance_mode,
                "targetRole": target_role.strip(),
                "experienceLevel": experience_level.strip(),
                "diagnostics": baseline.get("diagnostics", {}),
                "audioEvidence": baseline.get("audioEvidence", {}),
                **advanced,
            },
            "meta": {
                "modelPredictionSource": "saved-ml-pipeline",
                "guidanceSource": guidance_mode,
                "aiFallbackUsed": bool(ai_error),
            },
        }

    except HTTPException:
        raise
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Audio analysis failed: " + str(error),
        ) from error
    finally:
        try:
            await audio.close()
        except Exception:
            pass

        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


# ============================================================================
# COMPONENT 2: CAREERLENS (CV BASED CAREER PATH GUIDANCE)
# ============================================================================

def validate_job_search(job_role: str, location: str, limit: int):
    job_role = (job_role or "").strip()
    location = (location or "Sri Lanka").strip()

    if not job_role:
        raise HTTPException(status_code=400, detail="Job role is required")
    if limit < 1 or limit > 15:
        raise HTTPException(status_code=400, detail="Limit should be between 1 and 15")

    return job_role, location


@app.get("/api/jobs")
def get_jobs(
    job_role: str,
    location: str = "Sri Lanka",
    limit: int = 5,
):
    job_role, location = validate_job_search(job_role, location, limit)
    service = JobSearchService()

    result = service.search_all_sources(
        job_role=job_role,
        location=location,
        google_limit=limit,
        topjobs_limit=min(limit, 5),
        linkedin_limit=min(limit, 5),
    )

    return {
        "status": "success",
        "job_role": job_role,
        "location": location,
        "google_jobs": result["google_jobs"],
        "topjobs_jobs": result["topjobs_jobs"],
        "linkedin_jobs": result["linkedin_jobs"],
        "jobs": result["all_jobs"],
        "errors": result["errors"],
    }


@app.post("/api/analyze-cv")
async def analyze_cv(
    cv: UploadFile = File(...),
    job_role: str = Form(...),
    location: str = Form("Sri Lanka"),
    max_jobs: int = Form(5),
):
    try:
        job_role = job_role.strip()
        location = location.strip() if location else "Sri Lanka"

        if not job_role:
            raise ValueError("Please select a target job role")

        data = await cv.read()
        if not data:
            raise ValueError("The uploaded CV file is empty")

        filename = cv.filename or "cv.pdf"
        cv_text = extract_cv_text(filename, data)

        if len(cv_text.strip()) < 80:
            raise ValueError(
                "Unable to extract sufficient text from this CV. Please ensure the file is not a scanned image."
            )

        # 1. Deterministic CV Evidence Extraction
        cv_evidence = build_cv_evidence(cv_text)

        # 2. Supervised ML Career Path Prediction
        predicted_career_path = career_model.predict(cv_text)

        # 3. Live Job Retrieval from Google Jobs, TopJobs, LinkedIn
        search_service = JobSearchService()
        jobs_result = search_service.search_all_sources(
            job_role=job_role,
            location=location,
            google_limit=max_jobs,
            topjobs_limit=min(max_jobs, 5),
            linkedin_limit=min(max_jobs, 5),
        )

        # 4. Explainable Skill Evidence Comparison
        compared_jobs = compare_cv_to_jobs(
            cv_skills=cv_evidence.get("skills", []),
            target_role=job_role,
            jobs=jobs_result["all_jobs"],
        )

        # 5. Decoupled 2D CV Readiness Assessment
        readiness = readiness_service.assess(
            cv_evidence=cv_evidence,
            matched_jobs=compared_jobs,
            target_role=job_role,
            predicted_career_path=predicted_career_path,
        )

        # 6. Grounded Career Guidance
        guidance = GuidanceService().generate(
            target_role=job_role,
            predicted_career_path=predicted_career_path,
            cv_evidence=cv_evidence,
            readiness=readiness,
            jobs=compared_jobs,
        )

        return {
            "status": "success",
            "target_role": job_role,
            "location": location,
            "career_path_prediction": {
                "label": predicted_career_path,
                "method": "trained_supervised_nlp_pipeline",
                "model": career_model.metadata(),
            },
            "cv_readiness": readiness,
            "cv_evidence": cv_evidence,
            "guidance": guidance,
            "jobs": compared_jobs,
            "google_jobs": [j for j in compared_jobs if j.get("source_type") == "google_jobs"],
            "topjobs_jobs": [j for j in compared_jobs if j.get("source_type") == "topjobs"],
            "linkedin_jobs": [j for j in compared_jobs if j.get("source_type") == "linkedin_jobs"],
            "methodology": {
                "career_path": "Trained CV text classification model (TF-IDF + LinearSVC/Logistic Regression)",
                "cv_evidence": "Deterministic section & skill evidence extraction",
                "vacancies": "Google Jobs + TopJobs + LinkedIn Jobs real-time retrieval",
                "matching": "Explainable skill evidence comparison",
                "guidance": "Grounded AI career guidance with deterministic fallback",
                "numeric_score": False,
            },
        }

    except Exception as exc:
        print(f"[CV Analysis Error] {exc}")
        raise HTTPException(status_code=400, detail=str(exc))


# ============================================================================
# COMPONENT 3: CAREER RISK (CAREER SAFETY & INDUSTRY STABILITY ANALYSIS)
# ============================================================================

class CareerRiskPredictRequest(BaseModel):
    role: str
    years_experience: str
    tech_stack_change: int
    weekly_learning_time: str
    switch_confidence: int
    career_strategy: str
    skill_update_frequency: str


@app.post("/api/career-risk/predict")
def career_risk_predict(payload: CareerRiskPredictRequest):
    try:
        result = career_risk_service.predict(payload.model_dump())
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Risk estimation failed: {exc}")

    clean_payload = result.pop("cleanPayload")

    try:
        history_id = career_risk_history.save_assessment(clean_payload, result)
        result["historyId"] = history_id
    except Exception as history_error:
        result["historyWarning"] = str(history_error)

    return result


@app.get("/api/career-risk/history")
def career_risk_history_list(limit: int = Query(default=50, ge=1, le=100)):
    try:
        return {"items": career_risk_history.list_assessments(limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to load history: {exc}")


@app.get("/api/career-risk/history/{assessment_id}")
def career_risk_history_detail(assessment_id: int):
    item = career_risk_history.get_assessment(assessment_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return item


@app.delete("/api/career-risk/history/{assessment_id}")
def career_risk_history_delete(assessment_id: int):
    deleted = career_risk_history.delete_assessment(assessment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return {"message": "Assessment deleted.", "id": assessment_id}


# ============================================================================
# COMPONENT 4: EMPLOYABILITY SIMULATOR (BEHAVIOUR-AWARE CAREER SIMULATION)
# ============================================================================

def _get_employability_service(phase_id: str):
    service = employability_services.get(phase_id)
    if service is None:
        raise HTTPException(status_code=404, detail=f"Unknown employability phase: {phase_id}")
    return service


@app.get("/api/employability/{phase_id}/health")
def employability_health(phase_id: str):
    return _get_employability_service(phase_id).health()


@app.post("/api/employability/{phase_id}/predict")
def employability_predict(phase_id: str, responses: Dict[str, float]):
    service = _get_employability_service(phase_id)
    try:
        return service.predict(responses)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Employability prediction failed: {exc}")


class EmployabilityWhatIfRequest(BaseModel):
    responses: Dict[str, float]
    overrides: Dict[str, float]


@app.post("/api/employability/{phase_id}/what-if")
def employability_what_if(phase_id: str, request: EmployabilityWhatIfRequest):
    service = _get_employability_service(phase_id)
    try:
        return service.simulate(request.responses, request.overrides)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Employability what-if failed: {exc}")


# ============================================================================
# COMPONENT 5: HR CANDIDATE SELECTION (ADMIN-ONLY CANDIDATE VERIFICATION)
# ============================================================================

class HRRoleRequest(BaseModel):
    roleId: str
    roleName: str
    category: str
    requiredSkills: List[Dict[str, object]]
    preferredSkills: List[Dict[str, object]]


class HRDecisionRequest(BaseModel):
    decision: str
    notes: Optional[str] = ""
    reviewerName: Optional[str] = "Hiring Manager"


@app.get("/api/hr-candidates/health")
def hr_candidates_health(authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    return hr_candidate_service.health()


@app.get("/api/hr-candidates/roles")
def hr_candidates_get_roles(authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    return hr_candidate_service.get_roles()


@app.post("/api/hr-candidates/roles")
def hr_candidates_create_role(role: HRRoleRequest, authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    saved = hr_candidate_service.create_custom_role(role.model_dump())
    return {"status": "SUCCESS", "role": saved}


@app.get("/api/hr-candidates/skills/search")
def hr_candidates_search_skills(q: str, authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    return hr_candidate_service.search_skills(q)


@app.post("/api/hr-candidates/candidates/assess")
async def hr_candidates_assess_candidate(
    candidate_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    github_username: Optional[str] = Form(None),
    linkedin_url: Optional[str] = Form(None),
    apify_token: Optional[str] = Form(None),
    target_role_id: Optional[str] = Form("full_stack_mern"),
    resume_text: Optional[str] = Form(None),
    resume_file: Optional[UploadFile] = File(None),
    authorization: Optional[str] = Header(default=None),
):
    require_admin(authorization)

    file_bytes = None
    filename = "pasted_text.txt"
    if resume_file and resume_file.filename:
        file_bytes = await resume_file.read()
        filename = resume_file.filename

    try:
        record = hr_candidate_service.assess_candidate(
            filename=filename,
            file_bytes=file_bytes,
            resume_text=resume_text,
            candidate_name=candidate_name,
            email=email,
            github_username=github_username,
            linkedin_url=linkedin_url,
            apify_token=apify_token,
            target_role_id=target_role_id,
        )
        return record
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Candidate assessment failed: {exc}")


@app.get("/api/hr-candidates/candidates")
def hr_candidates_get_candidates(authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    return hr_candidate_service.get_candidates()


@app.get("/api/hr-candidates/candidates/{assessment_id}")
def hr_candidates_get_candidate_detail(assessment_id: str, authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    record = hr_candidate_service.get_candidate_detail(assessment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Candidate assessment record not found.")
    return record


@app.post("/api/hr-candidates/candidates/{assessment_id}/decision")
def hr_candidates_record_decision(
    assessment_id: str, decision: HRDecisionRequest, authorization: Optional[str] = Header(default=None)
):
    require_admin(authorization)
    record = hr_candidate_service.record_hr_decision(
        assessment_id, decision.decision, decision.notes or "", decision.reviewerName or "Hiring Manager"
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Candidate assessment record not found.")
    return {"status": "SUCCESS", "record": record}


@app.delete("/api/hr-candidates/candidates/{assessment_id}")
def hr_candidates_delete_candidate(assessment_id: str, authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    deleted = hr_candidate_service.delete_candidate(assessment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Candidate assessment record not found.")
    return {"status": "SUCCESS", "message": f"Candidate {assessment_id} deleted successfully."}


@app.get("/api/hr-candidates/ablation")
def hr_candidates_get_ablation_results(authorization: Optional[str] = Header(default=None)):
    require_admin(authorization)
    return hr_candidate_service.get_ablation_results()


# ============================================================================
# STATIC FRONTEND MOUNTING & SPA ROUTE FALLBACK
# ============================================================================

if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API routes to be handled by FastAPI
        if full_path.startswith("api/") or full_path in ["health", "docs", "openapi.json"]:
            raise HTTPException(status_code=404, detail="Not Found")
        
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        return JSONResponse(
            {"message": "Career Intelligence Platform API is running. Build frontend to access the UI."},
            status_code=200,
        )
else:
    @app.get("/")
    def root():
        return {
            "status": "ok",
            "message": "Career Intelligence Platform API running on port 8000. Frontend assets will be served from app/static.",
            "endpoints": {
                "health": "/health",
                "modules": "/api/modules",
                "analyze_audio": "/api/analyze/audio",
                "coach_follow_up": "/api/coach/follow-up",
                "analyze_cv": "/api/analyze-cv",
                "jobs": "/api/jobs",
                "career_risk_predict": "/api/career-risk/predict",
                "employability_predict": "/api/employability/{phase_id}/predict",
                "employability_what_if": "/api/employability/{phase_id}/what-if",
                "hr_candidates_assess": "/api/hr-candidates/candidates/assess (admin only)",
                "docs": "/docs",
            },
        }
