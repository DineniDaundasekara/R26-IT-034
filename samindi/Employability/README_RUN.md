# Employability Simulator — local run notes

Behaviour-aware employability prediction from three frozen models:

| Phase | Domain | Model |
| --- | --- | --- |
| 01 | Internship experience | XGBoost |
| 02 | Competence | Linear regression |
| 03 | Psychological capital | ElasticNet |

## Preferred: unified platform

From the repository root:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000 → **Career Simulation** (Employability).

API examples:

- `GET /api/employability/phase1/health`
- `POST /api/employability/phase1/predict`
- `POST /api/employability/phase1/what-if`

## Standalone frontend (optional)

```powershell
cd samindi/Employability/frontend
npm install
npm run dev
```

Point `VITE_API_URL` at the unified backend (`http://127.0.0.1:8000`).

## Environment

```powershell
copy .env.example .env
```

Put your OpenAI key in `.env` only for guidance text. The employability score always comes from the frozen ML model.
