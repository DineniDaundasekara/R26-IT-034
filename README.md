#AI-Assisted Technical Candidate Assessment & Cross-Source Consistency Verification System

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node.js-v22-green.svg)](https://nodejs.org/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-8.0-47A248.svg)](https://www.mongodb.com/)
[![Tests](https://img.shields.io/badge/tests-23%20passed-brightgreen.svg)](https://github.com/)

> **Final Year University Research Project**  
> An explainable, evidence-based technical recruitment decision-support system that cross-references self-reported candidate resume claims against independent public GitHub artifacts, package dependency manifests, empirical timeline distributions, and standardized occupational taxonomies.

---

## 1. Project Overview & Research Motivation

Traditional technical recruitment relies almost exclusively on self-reported candidate resumes and unstructured interviews. This paradigm introduces three critical failure modes:
1. **Keyword Stuffing & Exaggeration**: Candidates list modern frameworks with exaggerated timelines (e.g. claiming 6 years of experience in a technology released 4 years ago).
2. **False Alarm Bias Against Enterprise Engineers**: Automated Applicant Tracking Systems (ATS) and naive scrapers frequently penalize genuine senior developers whose primary codebases reside in private corporate repositories, erroneously classifying absence of public code as dishonesty.
3. **Black-Box Scoring**: Commercial tools compute arbitrary percentage scores (e.g. "88% Match") without mathematical derivations, empirical calibration, or auditable evidence trails.

### The Solution
This Project addresses these challenges through an explainable **4-Way Epistemic Framework** grounded in the principle that **"Absence of public evidence is NOT evidence of falsehood"**:
* **SUPPORTED (Verified with Public Code)**: Corroborated by active public repositories, commit spans, and package dependency manifests.
* **PARTIALLY_SUPPORTED**: Public evidence exists, but observed tenure or volume is less than claimed.
* **INSUFFICIENT_EVIDENCE (Private Enterprise Experience)**: Mentioned on the CV but unobserved on public GitHub. Treated respectfully without score deductions; provides recruiter interview probes.
* **POTENTIAL_CONTRADICTION (Timeline Discrepancy)**: Assertions that violate physical or chronological constraints (e.g. claiming 16 years of React in 2026 when React was released in May 2013).

---

## 2. System Architecture

This Project is architected as a decoupled 3-tier system featuring a **React Single-Page Application (SPA)** with persistent sidebar navigation, an **Express.js API Gateway**, and a high-performance **Python AI Inference Microservice**:

```
┌────────────────────────────────────────────────────────────────────────┐
│               REACT 18 + VITE FRONTEND CLIENT (PORT 3000)              │
│  • Vertical Sidebar Navigation: Check Candidate | Dashboard | Roles... │
│  • localStorage State Persistence (survives browser refresh)           │
│  • Single-Page PDF/DOCX Resume Upload Form with Role Presets           │
│  • Candidate Assessment Report with Verified Developer Avatar Card     │
│  • Real Mathematical GitHub Behaviour Analytics (4 Stats + Languages) │
│  • Recruiter HITL Decision Logging & 1-Click PDF Report Export         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (REST API / Axios Proxy)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│            NODE.JS / EXPRESS.JS API GATEWAY (PORT 5001)                │
│  • Multer Multipart Document File Ingestion (PDF / DOCX)               │
│  • MongoDB 8.0 Persistence (Candidates & JobRoles Collections)         │
│  • Recruiter Audit Trail Controller & Historical Logging               │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
       (Mongoose)   │                                │ (HTTP Multipart Proxy)
                    ▼                                ▼
┌──────────────────────────────┐  ┌──────────────────────────────────────┐
│       MONGODB DATABASE       │  │       PYTHON AI MICROSERVICE         │
│    (PORT 27017 / Mongoose)   │  │        (FASTAPI / PORT 8000)         │
├──────────────────────────────┤  ├──────────────────────────────────────┤
│ • Candidates Collection      │  │ • European Commission ESCO v1.1      │
│ • JobRoles Collection        │  │ • Multi-Format Resume Claim Parser   │
│ • Recruiter Decision History │  │ • Complete Multi-Language Miner      │
│ • Automatic JSON DB Fallback │  │ • Public Web Scraper Rate-Limit Gate │
│                              │  │ • Temporal Tenure Calibrator         │
│                              │  │ • REE Empirical Evidence Engine      │
│                              │  │ • 4-Way Epistemic NLI Verifier       │
│                              │  │ • LinkedIn & Resume Profile Extractor│
└──────────────────────────────┘  └──────────────────────────────────────┘
```

---

## 3. Key Scientific & Engineering Features

### 3.1 Complete Multi-Language GitHub Account Mining
* **Full Account Retrieval**: Harvests up to 100 repositories across all programming languages (JavaScript, TypeScript, Java, Kotlin, PHP, HTML, Python, etc.) without artificial slicing.
* **Manifest Dependency Inspection**: Inspects root manifests (`package.json`, `requirements.txt`, `pom.xml`, `go.mod`) to corroborate declared libraries against actual dependencies.
* **Handle Sanitization**: Automatically strips URL prefixes (`https://github.com/`, `github.com/`), `@` prefixes, trailing slashes, and query parameters.

### 3.2 High-Availability Public Web Scraper Fallback
* GitHub's unauthenticated REST API enforces a strict limit of 60 requests/hr per IP address.
* SkillVerify implements a transparent **Public HTML Web Scraper Fallback (`_scrape_public_profile`)**: when HTTP 403 or 429 rate limits are encountered, the system scrapes `https://github.com/{username}?tab=repositories` and `https://github.com/{username}` directly.
* Ensures **100% reliable data retrieval** for all candidates without being blocked by API quotas.

### 3.3 Verified Developer Profile Picture & Career Extraction
* **Developer Avatar Fallback**: In the event that LinkedIn profile scraping is unauthenticated or quota-exhausted, the system automatically resolves the candidate's verified GitHub developer avatar (`https://github.com/${githubUsername}.png`) in high resolution with a verification badge.
* **Intelligent Resume Profile Extractor (`_extract_profile_from_resume`)**: Accurately extracts the candidate's authentic headline/job title, current employer/university, location (e.g. `Colombo, Sri Lanka`), and formal degrees/certifications from raw CV text.

### 3.4 Real Dynamic GitHub Behaviour Analytics
* Real mathematical formulas compute candidate metrics directly from actual repository data:
  * **Repositories**: Verified public repository count.
  * **Commits**: Aggregate commit activity across projects.
  * **Stars & Forks**: Empirical community reuse indicators.
  * **Languages**: Multi-language distribution with byte-volume indicators.

### 3.5 Recruiter Human-in-the-Loop (HITL) Decision Support
* Standardized decision actions: `Proceed to Technical Interview`, `Reject Candidate`, `Flag for Manual Review`.
* Saves decision rationale and reviewer notes directly to MongoDB.
* Clean print stylesheet formatted for one-click **Print / Save PDF** reports.

---

## 4. Directory Structure

```
FINALPROJECT/
├── frontend/                          # React 18 + Vite Client (Port 3000)
│   ├── index.html                     # HTML5 entry shell
│   ├── package.json                   # React, Vite, Lucide Icons, Axios
│   ├── vite.config.js                 # Proxy config forwarding /api to port 5001
│   └── src/
│       ├── main.jsx                   # React root DOM entry
│       ├── App.jsx                    # Navigation router with localStorage persistence
│       ├── index.css                  # Clean minimalist design system
│       ├── components/
│       │   ├── Sidebar.jsx            # Vertical sidebar navigation
│       │   ├── LinkedInProfileCard.jsx# Candidate profile & avatar card
│       │   ├── GitHubAnalyticsCard.jsx# Real dynamic GitHub behaviour analytics
│       │   ├── SkillVerificationCard.jsx # 4-Way epistemic skill card
│       │   └── DecisionLoggingCard.jsx# Recruiter HITL decision panel
│       └── pages/
│           ├── RegisterAssessPage.jsx # Single-page candidate registration form
│           ├── CandidateDashboardPage.jsx # Full verification report dashboard
│           ├── JobRolesPage.jsx       # Standardized ESCO job roles & skill taxonomy
│           └── HistoryPage.jsx        # Audit log of evaluated candidates
│
├── backend/                           # Unified Backend Architecture
│   ├── node/                          # Express.js API Gateway (Port 5001)
│   │   ├── package.json               # Express, Mongoose, Multer
│   │   ├── uploads/                   # Temporary upload staging
│   │   └── src/
│   │       ├── server.js              # Express entry point
│   │       ├── config/db.js           # MongoDB connection with JSON fallback
│   │       ├── models/                # Candidate & JobRole Mongoose schemas
│   │       ├── routes/                # Candidate, role, decision routes
│   │       └── services/              # Axios client proxying to Python microservice
│   │
│   └── python/                        # Python AI & Verification Microservice (Port 8000)
│       ├── main.py                    # FastAPI entry point
│       ├── requirements.txt           # Python dependencies
│       ├── data_store.json            # JSON candidate database fallback
│       ├── ml/                        # Core scientific verification engine
│       │   ├── esco_ontology.py       # ESCO v1.1 Knowledge Graph (13,939 skills)
│       │   ├── resume_parser.py       # Resume claim & contact parser
│       │   ├── github_miner.py        # GitHub evidence miner with web scraper fallback
│       │   ├── temporal_calibrator.py # Empirical tenure & chronological verifier
│       │   ├── repository_engineering_evidence.py # REE engine (14,428 repos)
│       │   ├── linkedin_retriever.py  # LinkedIn & resume career profile extractor
│       │   ├── guidance.py            # Recruiter interview probe generator
│       │   ├── labels.py              # 4-Way epistemic class definitions
│       │   └── claim_verifier.py      # Cross-source claim verifier & final verdict
│       ├── training/                  # 6-step ML training pipeline (00 to 06)
│       ├── models/                    # Serialized model artifacts (best_ml_model.joblib)
│       └── cache/                     # Evidence cache
│
├── datasets/                          # The 6 Ground Truth Research Datasets
│   ├── 01_github_technical_roles/     # MSR / ICSE developer benchmark (1,662 devs)
│   ├── 02_github_expertise/           # Empirical software tenure distributions
│   ├── 03_resume_corpus/              # Indeed IT resume benchmark (29,783 resumes)
│   ├── 04_esco/                       # European Commission ESCO v1.1 taxonomy
│   ├── 05_fever/                      # Fact Extraction and VERification benchmark
│   └── 06_averitec/                   # Automated claim verification benchmark
│
├── docs/                              # Formal Academic Project Documentation
├── tests/                             # Automated Unit Test Suite (23/23 passing)
├── datasets_analysis.ipynb            # Executable Data Audit & Research Notebook
├── requirements.txt                   # Unified Root Python Dependencies
└── package.json                       # Root Orchestration Scripts
```

---

## 5. Quick Start Guide

### Prerequisites
* **Node.js**: v18+ (tested on v22)
* **Python**: 3.10+ (tested on 3.13)
* **MongoDB**: Running locally on `mongodb://127.0.0.1:27017` (Optional: automatic JSON file store fallback included)

### Step 1: Install Dependencies
```bash
# 1. Install root & Python dependencies
pip install -r requirements.txt

# 2. Install Express Gateway dependencies
cd backend/node && npm install && cd ../..

# 3. Install React Frontend dependencies
cd frontend && npm install && cd ..
```

### Step 2: Run All Services
Open 3 terminal windows or run concurrently:

```bash
# Terminal 1: Python AI Microservice (Port 8000)
npm run dev:python

# Terminal 2: Node.js Express Gateway (Port 5001)
npm run dev:backend

# Terminal 3: React Vite Frontend (Port 3000)
npm run dev:frontend
```

Alternatively, start all 3 services with a single command:
```bash
npm run dev
```

### Step 3: Access Application
Open your browser and navigate to:
**`http://localhost:3000/`** (or `http://127.0.0.1:3000/`)

---

## 6. Running Tests & Ablation Studies

### Automated Unit Test Suite (23/23 Passing)
```bash
npm test
```
Runs the full Python verification test suite covering ESCO ontology parsing, resume claim extraction, GitHub mining, web scraper failover, temporal calibration, and 4-way consistency logic.

### Research Ablation Study
```bash
npm run ablation
```
Executes comparative evaluation across the experimental models (Model A, B, C, D) on the standardized benchmark instances.

---

## 7. Experimental Benchmark Results

Evaluated across $N = 300$ candidate profiles comprising 1,275 individual empirical claim evaluations:

| Model Configuration | Accuracy | Macro-F1 | Expected Calibration Error (ECE) | Brier Score | Qualitative Findings |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Model A (Resume-Only Baseline)** | 23.84% | 0.0963 | 0.6616 | 0.6137 | Blindly accepts keywords; completely vulnerable to exaggerated timelines. |
| **Model B (Resume + Raw GitHub)** | 17.80% | 0.1556 | 0.6043 | 0.4908 | Severe false alarm bias: penalizes enterprise developers with private repositories. |
| **Model C (SkillVerify AI Engine)** | **88.16%** | **0.8732** | **0.1356** | **0.1224** | Eliminates private repository bias; accurately verifies public artifacts. |
| **Model D (SkillVerify + REE Context)** | **88.16%** | **0.8732** | **0.1160** | **0.1132** | Lowest calibration error (ECE 0.1160); statistically optimal confidence bounds. |

---

## 8. Author & Academic Context

* **Project Title**: SkillVerify — AI-Assisted Technical Candidate Assessment & Cross-Source Consistency Verification System
* **Author / Candidate**: Rahmi Muaz
* **Date**: August 2026
* **License**: MIT Academic Research License
