# CareerLens Backend

This clean backend keeps the trained career-path model and prepared research datasets, but does not duplicate the raw CV PDF corpus or your secret `.env` file.

## Main flow

CV upload → text extraction → career-path prediction → CV evidence extraction → Google Jobs + TopJobs public vacancy retrieval → matched/missing skill evidence → qualitative CV readiness → professional career/CV guidance → public vacancy links.

## 1. Create `.env`

Copy `.env.example` to `.env` and enter NEW keys:

```env
SERPAPI_KEY=YOUR_NEW_SERPAPI_KEY
GROQ_API_KEY=YOUR_NEW_GROQ_KEY
GROQ_MODEL=llama-3.3-70b-versatile
```

Never commit `.env`.

## 2. Install

```powershell
cd "<YOUR PROJECT>\backend"
python -m pip install -r requirements.txt
```

## 3. Run

```powershell
python -m uvicorn app:app --reload --port 8000
```

Open:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/docs

## Job endpoints

- `GET /api/jobs/google` — structured Google Jobs results via SerpApi.
- `GET /api/jobs/topjobs` — publicly indexed TopJobs vacancy links found through SerpApi Google Search.
- `GET /api/jobs` — both sources.
- `POST /api/analyze-cv` — complete CV analysis and job recommendation pipeline.

## TopJobs design

The backend does not directly scrape TopJobs pages. It searches publicly indexed TopJobs URLs and returns the original TopJobs link when available. If no direct indexed result is found, the frontend provides a TopJobs search/portal fallback.

## Existing training artifacts included

- `models/best_cv_guidance_model.pkl`
- model comparison/result files
- prepared CSV training/evaluation datasets
- original training scripts

Raw personal CV PDFs are intentionally not duplicated into this clean downloadable package. If you need to retrain, place your existing CV corpus in `data/cvs/`.
