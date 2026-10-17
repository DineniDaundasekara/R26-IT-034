import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

COMMUNICATION_APP_URL = os.getenv(
    "COMMUNICATION_APP_URL", "http://127.0.0.1:5173"
).rstrip("/")
CAREER_APP_URL = os.getenv(
    "CAREER_APP_URL", "http://127.0.0.1:5174"
).rstrip("/")
EMPLOYABILITY_APP_URL = os.getenv(
    "EMPLOYABILITY_APP_URL", "http://127.0.0.1:8000/employability-simulation"
).rstrip("/")
CAREER_RISK_APP_URL = os.getenv(
    "CAREER_RISK_APP_URL", "http://127.0.0.1:8000/career-risk"
).rstrip("/")

app = FastAPI(
    title="Interview Readiness & Career Path Dashboard API",
    version="1.1.0",
    description=(
        "Gateway for the AI-driven interview readiness, career path, "
        "career safety, and employability simulation modules."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5180",
        "http://127.0.0.1:5180",
        "http://localhost:5181",
        "http://127.0.0.1:5181",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MODULES = [
    {
        "id": "communication",
        "title": "Communication skill guidance",
        "subtitle": "InterviewReady",
        "description": (
            "Practice spoken interview answers, get communication-level feedback, "
            "and receive AI coaching to improve interview readiness."
        ),
        "url": COMMUNICATION_APP_URL,
        "folder": "InterviewReady/nlp-component/frontend",
    },
    {
        "id": "career",
        "title": "CV based career path guidance",
        "subtitle": "CareerLens",
        "description": (
            "Upload a CV, match it to current job roles, and get explainable "
            "career-path guidance based on your evidence and skill gaps."
        ),
        "url": CAREER_APP_URL,
        "folder": "component 2-with frontend/frontend",
    },
    {
        "id": "career-risk",
        "title": "Career safety and industry stability",
        "subtitle": "Career Safety AI",
        "description": (
            "Assess automation exposure, industry stability, and skill "
            "transferability with explainable risk categories."
        ),
        "url": CAREER_RISK_APP_URL,
        "folder": "CareerRisk/frontend",
    },
    {
        "id": "employability",
        "title": "Behaviour-aware employability simulation",
        "subtitle": "Employability Simulator",
        "description": (
            "Predict employability from internship experience, competence, "
            "and psychological capital using frozen ML models and grounded guidance."
        ),
        "url": EMPLOYABILITY_APP_URL,
        "folder": "Employability/frontend",
    },
]


async def probe_url(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=1.5, follow_redirects=True) as client:
            response = await client.get(url)
        return response.status_code < 500
    except Exception:
        return False


@app.get("/")
def root():
    return {
        "success": True,
        "message": (
            "AI-driven interview readiness, career path, career safety, "
            "and employability simulation dashboard API is running."
        ),
        "version": "1.1.0",
    }


@app.get("/health")
def health():
    return {"success": True, "status": "ok"}


@app.get("/api/modules")
async def list_modules():
    items = []
    for module in MODULES:
        available = await probe_url(module["url"])
        items.append({**module, "available": available})
    return {"success": True, "modules": items}
