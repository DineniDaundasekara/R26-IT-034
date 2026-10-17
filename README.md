# Career Intelligence Platform
## Comprehensive Career Development and Recruitment Framework

A unified, production-ready research platform developed for final-year research presentation and viva panel demonstration.

---

## 1. Quick Start (Single Command)

To run the full integrated project with both frontend and backend on port 8000:

```powershell
# From the project root
python -m uvicorn app.main:app --reload --port 8000
```

Or double-click `run_app.bat` to launch the server and open the browser automatically.

- **Main Dashboard & Application**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 2. System Architecture & Page Flow

When you open **http://127.0.0.1:8000**, sign in (or create an account). After a successful login you are taken to the **Home** page, with a top navigation bar for all four research modules:

```
                                          ┌───────────────────────────┐
                                          │      Main Dashboard       │
                                          │   (http://127.0.0.1:8000) │
                                          └─────────────┬─────────────┘
                                                          │
          ┌─────────────────────┬─────────────────────┬─┴───────────────────┐
          ▼                     ▼                     ▼                     ▼
 ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
 │ Interview         │ │ Career Path       │ │ Career Safety &   │ │ Employability     │
 │ Readiness         │ │ Guidance          │ │ Industry Stability│ │ Simulator         │
 │ (InterviewReady)  │ │ (CareerLens)      │ │ (Career Safety AI)│ │ (Career Simulation)│
 └────────┬──────────┘ └────────┬──────────┘ └────────┬──────────┘ └────────┬──────────┘
          │                     │                     │                     │
 • Live Audio Recording  • PDF/DOCX/TXT CV     • Career Profile      • Internship, Competence
   / WAV Upload            Upload & Parsing      Questionnaire         & PsyCap Assessments
 • Faster-Whisper ASR    • Supervised Career-  • Random Forest       • XGBoost / Linear
 • 9 Acoustic Features     Path Classifier       Risk Classifier       Regression / ElasticNet
 • Supervised ML         • Decoupled 2D CV     • Auxiliary Indicator • Construct-Level
   Communication Model     Evaluation Matrix     Sub-Models            Explainability
 • STAR Framework &      • Real-Time Google/   • Explainable Risk    • Personalized
   Linguistic Analysis     TopJobs/LinkedIn      Factor Mapping        Development Guidance
 • Grounded AI Coach     • Grounded AI Action  • 30/60/90-Day AI
   & Rewrite Lab           Guidance              Resilience Plan
```

### Navigation & Routing
- **Sign in / Register** is required before entering the workspace.
- After login, **Home** shows all four research modules as cards and as navbar tabs.
- Clicking **"Interview Readiness"** (card or tab) opens InterviewReady.
- Clicking **"Career Path Guidance"** (card or tab) opens CareerLens.
- Clicking **"Career Safety"** (card or tab) opens the Career Safety AI module.
- Clicking **"Career Simulation"** (card or tab) opens the Employability Simulator.
- The global top navigation bar allows 1-click return to **Home** at any time.
- Viva demo account: `demo@pathready.ai` / `PathReady2026`

### Role-Based Access (Admin-Only HR Module)
- All accounts default to the `user` role and see the four modules above.
- A fifth module, **HR Candidate Selection**, is admin-only: it is hidden from the navbar and
  Home cards for regular users, and every `/api/hr-candidates/*` endpoint independently rejects
  non-admin tokens server-side (not just a hidden UI tab).
- Admin accounts are seeded server-side only — there is no self-service way to register as admin.
- Admin demo account: `hr@career-intel.ai` / `CareerIntel2026`

---

## 3. Component Details & Viva Talking Points

### Component 1: Interview Readiness & Communication Guidance (InterviewReady)
- **ASR Pipeline**: Faster-Whisper automatic speech recognition with VAD filtering.
- **Multi-Modal Feature Extraction**:
  - *Acoustic Signals*: Speaking rate (WPM), silence ratio (%), pause count, pause duration, audio energy dynamics.
  - *Linguistic / Discourse*: STAR framework component detection (Situation, Task, Action, Result), ownership phrasing, action verbs, and filler word density.
- **Classification Model**: Trained supervised pipeline (`communication_pipeline.joblib`) predicting **Poor**, **Average**, **Good**, or **Excellent Communication**.
- **Evidence-Grounded Coaching**: STAR structural coach, professional rewrite lab, sentence patterns, personalized practice answer with text-to-speech listener, 7-day practice sprint with local progress tracker, and interactive AI follow-up chat.

### Component 2: Career Path Guidance (CareerLens)
- **CV Text Extraction**: Deterministic PDF / DOCX / TXT extraction and section segmentation (Summary, Education, Experience, Skills, Projects).
- **Trained Career-Path Classifier**: Supervised TF-IDF n-gram classification model (`best_cv_guidance_model.pkl`) mapping candidate profiles into 9 primary engineering domains:
  * Software Engineer, Frontend Developer, Backend Developer, Full Stack Developer, QA Engineer, DevOps Engineer, Data Analyst, Business Analyst, UI/UX Designer.
- **Decoupled 2D Assessment Matrix**:
  - *Intrinsic Document Structural Quality*: Evaluates presence of core CV sections and professional portfolio links (Complete / Moderate / Needs attention).
  - *Extrinsic Target Role Alignment*: Evaluates alignment with market vacancies and explicitly flags **Career Transitions** when transitioning between domains.
- **Real-Time Job Vacancy Retrieval & Explainability**:
  - Multi-source search across **Google Jobs**, **TopJobs**, and **LinkedIn Jobs**.
  - Matched skills vs missing skills catalog comparison for clear upskilling guidance.

### Component 3: Career Safety & Industry Stability Analysis (Career Safety AI)
- **Career Profile Questionnaire**: Role, years of experience, tech-stack change exposure, weekly learning time, switch confidence, career strategy, and skill-update frequency.
- **Trained Risk Classifier**: Supervised Random Forest pipeline (`career_risk_model.pkl`) predicting an explainable **Overall Career Risk Level** (Low / Moderate / High Risk) — the single ML-sourced prediction in the report.
- **Auxiliary Indicator Sub-Models**: Separate trained estimators (`simplified_auxiliary_indicator_models.pkl`) infer automation exposure, industry/domain stability, and job market trend, which feed system-derived explanation indicators (learning activity, skill-update behavior, role-switching confidence, adaptability score, etc.).
- **Grounded AI Career Guidance**: OpenAI-generated, JSON-constrained Section 3 guidance — explainable recommendation, main risky areas, career strengths, stability/transferability/adaptability insights, risk-factor-to-recommendation mapping, and a personalized **30/60/90-day AI Career Resilience Action Plan** — with a deterministic "guidance unavailable" fallback when no AI key is configured.
- **Assessment History & Reporting**: Every generated report is saved to a local SQLite history store, reloadable from the UI, plus a one-click downloadable PDF report.
- Decision-support framing throughout: this module estimates career risk for planning purposes and explicitly does not predict job loss or make final career decisions.

### Component 4: Employability Simulator (Behaviour-Aware Career Simulation)
- **Three Independent Assessment Phases**, each backed by a frozen, validated regression model:
  - *Phase 1 — Internship Experience → Employability*: 12-item internship quality assessment (objectives, school support, workplace environment, career development) scored by a trained **XGBoost** model.
  - *Phase 2 — Competence → Employability*: 10-item life/career, learning/innovation, and IT/media skills assessment scored by a trained **Linear Regression** model.
  - *Phase 3 — Psychological Capital → Employability*: 12-item hope, optimism, resilience, and self-efficacy assessment scored by a trained **ElasticNet** model.
- **Construct-Level Explainability**: Each phase decomposes the overall prediction into construct scores with a Strong / Developing / Needs Improvement guidance level.
- **Personalized Development Guidance**: Top strengths and priority development areas, each with a concrete, actionable next step — never an artificial improvement percentage.

### Component 5: HR Candidate Selection (Admin Only)
- **Access Control**: Visible only to accounts with the `admin` role; every backend endpoint independently verifies the admin role (see Role-Based Access above).
- **Cross-Source Evidence Verification**: Cross-references a candidate's resume claims against independent public GitHub repositories, commit history, and package dependency manifests — not another self-reported score.
- **Direct LinkedIn Profile Lookup**: Retrieves profile picture, current role, and listed certifications via a live Apify scraper run (with a deterministic offline fallback when no API token is configured).
- **ESCO v1.1 Knowledge Graph**: Grounds skill canonicalization and five standard job-role profiles (Full Stack MERN, Backend Python, Frontend React, DevOps & Cloud, Data Engineer).
- **4-Way Epistemic Claim Verification**: Every claimed skill is classified as `SUPPORTED`, `PARTIALLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE` (private work — not penalized), or `POTENTIAL_CONTRADICTION` (chronological impossibility).
- **Repository Engineering Evidence**: Maintenance, collaboration, and activity-maturity analysis across a candidate's top public repositories.
- **Recruiter Decision Support**: Auto-generated technical interview probes, a recruiter verdict card, and a human-in-the-loop decision panel (shortlist / reject / request clarification) logged to an audit history.

---

## 4. Live Viva Demonstration Guide

1. **Step 1: Sign in and open Home**
   - Run `python -m uvicorn app.main:app --reload --port 8000`.
   - Sign in with the demo account (or register a new account). The app then opens the Home page.
   - Show the panel the unified portal, navbar tabs, and four-component architecture.
2. **Step 2: Demonstrate Interview Readiness & Communication Guidance**
   - Click **"Interview Readiness"**.
   - Record a 30-second live response or upload a sample recording (`samindi/InterviewReady/nlp-component/backend/data/training_audio/1.wav`).
   - Highlight the Faster-Whisper transcript, the predicted communication level, the acoustic diagnostics table (WPM, silence ratio, pitch), STAR discourse tags, and the grounded coaching rewrites.
   - Click the top **"Home"** tab to return to the home page.
3. **Step 3: Demonstrate Career Path Guidance**
   - Click **"Career Path Guidance"**.
   - Upload a sample CV (`samindi/component 2-with frontend/backend/data/cvs/1.pdf`), choose a target role (e.g. *Software Engineer*), and click **"Analyze CV & Find Jobs"**.
   - Highlight the ML career-path prediction, the decoupled 2D matrix, the detected skill chips, the live vacancies with matched/missing skill chips, and grounded guidance.
   - Click **"Home"** to return to the home page.
4. **Step 4: Demonstrate Career Safety & Industry Stability Analysis**
   - Click **"Career Safety"**.
   - Fill in the career profile questionnaire (role, experience, tech-stack change, learning time, switch confidence, career strategy, skill-update frequency) and click **"Generate Career Safety Report"**.
   - Highlight the Random Forest risk prediction, the system-derived explanation indicators, the AI career resilience action plan (30/60/90-day), the recommendation mapping table, the saved assessment history, and the downloadable PDF report.
   - Click **"Home"** to return to the home page.
5. **Step 5: Demonstrate the Employability Simulator**
   - Click **"Career Simulation"**.
   - Choose one of the three phases (Internship Experience, Competence, or Psychological Capital) and complete the short assessment.
   - Highlight the predicted employability score, the construct-level breakdown, and the personalized strengths/development guidance.
   - Click **"Back to Home"** to conclude the demonstration.
6. **Step 6 (Optional): Demonstrate Role-Based Access & HR Candidate Selection**
   - Sign out, then sign in with the admin account (`hr@career-intel.ai` / `CareerIntel2026`) to show the **"HR Candidates"** tab appearing only for this role.
   - Click **"HR Candidates"**, upload a sample resume with a GitHub username (and optionally a LinkedIn URL), select a target role, and click **"Verify Candidate Skills"**.
   - Highlight the LinkedIn profile card, the recruiter verdict, the per-skill GitHub evidence, the GitHub behaviour analytics, and the human-in-the-loop decision panel.
   - Sign back in with the regular demo account to show the tab disappearing again.

---

## 5. Unified API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the unified SPA (Login, Home, InterviewReady, CareerLens, Career Safety AI, Employability Simulator) |
| `POST` | `/api/auth/register` | Create a research workspace account |
| `POST` | `/api/auth/login` | Sign in and receive a session token |
| `GET` | `/api/auth/me` | Restore the signed-in user session |
| `POST` | `/api/auth/logout` | End the current session |
| `GET` | `/health` or `/api/health` | Comprehensive health check for ML models and API keys |
| `GET` | `/api/modules` | Metadata and features of all four research modules |
| `POST` | `/api/analyze/audio` | Spoken audio transcription, ML classification & guidance |
| `POST` | `/api/coach/follow-up` | Interactive grounded AI coach questions |
| `POST` | `/api/analyze-cv` | CV text extraction, career path prediction & job matching |
| `GET` | `/api/jobs` | Real-time vacancies from Google Jobs, TopJobs & LinkedIn |
| `POST` | `/api/career-risk/predict` | Career risk classification, system-derived indicators & AI guidance |
| `GET` | `/api/career-risk/history` | List saved career risk assessments |
| `GET` | `/api/career-risk/history/{id}` | Retrieve one saved career risk assessment |
| `DELETE` | `/api/career-risk/history/{id}` | Delete one saved career risk assessment |
| `GET` | `/api/employability/{phase_id}/health` | Health check for one employability phase model |
| `POST` | `/api/employability/{phase_id}/predict` | Employability prediction & construct-level guidance for a phase (`phase1`/`phase2`/`phase3`) |
| `GET`/`POST` | `/api/hr-candidates/roles` | *(admin only)* List / create job role profiles |
| `GET` | `/api/hr-candidates/skills/search` | *(admin only)* ESCO skill lookup & canonicalization |
| `POST` | `/api/hr-candidates/candidates/assess` | *(admin only)* Resume vs. GitHub/LinkedIn cross-source candidate verification |
| `GET` | `/api/hr-candidates/candidates` | *(admin only)* List all verified candidates (audit history) |
| `GET` | `/api/hr-candidates/candidates/{id}` | *(admin only)* Retrieve one candidate assessment record |
| `POST` | `/api/hr-candidates/candidates/{id}/decision` | *(admin only)* Record a recruiter HITL hiring decision |
| `DELETE` | `/api/hr-candidates/candidates/{id}` | *(admin only)* Delete a candidate assessment record |
| `GET` | `/api/hr-candidates/ablation` | *(admin only)* Empirical ablation study results (Models A/B/C) |
