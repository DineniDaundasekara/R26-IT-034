# CV Guidance + Real-World Job Matching Patch

This patch is designed for the backend structure shown in your screenshots:

- `backend/data/`
- `backend/models/best_cv_guidance_model.pkl`
- `backend/scripts/`
- `backend/.env`
- `frontend/`

It keeps your **trained CV classifier** as the readiness decision layer and adds a separate **live job-market evidence layer**. The user sees categories and guidance, not a made-up CV percentage.

## 0. Security first

The API keys pasted into chat should be treated as exposed. Revoke/regenerate both keys before continuing. Put only the new keys in `backend/.env`. Do not commit `.env` to GitHub.

Example:

```env
GROQ_API_KEY=YOUR_NEW_GROQ_KEY
SERPAPI_KEY=YOUR_NEW_SERPAPI_KEY
GROQ_MODEL=llama-3.3-70b-versatile
```

## 1. Copy the patch into your existing project

Copy these into your current `backend` folder:

```text
app.py
requirements_cv_guidance.txt
services/
scripts/test_cv_guidance.py
scripts/inspect_saved_cv_model.py
scripts/fetch_google_jobs.py   # replace your old one if you want the same output schema
```

Do **not** delete your existing `data/`, `models/`, or training scripts.

Your important trained artifact must remain here:

```text
backend/models/best_cv_guidance_model.pkl
```

## 2. Install packages

In PowerShell:

```powershell
cd "C:\Users\User\Desktop\research-component-2\component 2-with frontend\backend"
python -m pip install -r requirements_cv_guidance.txt
```

## 3. Verify your saved model accepts raw CV text

```powershell
cd "C:\Users\User\Desktop\research-component-2\component 2-with frontend\backend\scripts"
python inspect_saved_cv_model.py
```

Best output is an sklearn `Pipeline` with a text vectorizer step and a classifier step.

If it says the model is not a pipeline, update each training script so the saved object is the entire pipeline, for example:

```python
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(...)),
    ("classifier", RandomForestClassifier(...)),
])
pipeline.fit(X_train, y_train)
joblib.dump(pipeline, MODEL_FILE)
```

Then rerun your existing training command order and `compare_best_cv_model.py`.

## 4. Start the backend API

```powershell
cd "C:\Users\User\Desktop\research-component-2\component 2-with frontend\backend"
python -m uvicorn app:app --reload --port 8000
```

Test:

```text
http://127.0.0.1:8000/health
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## 5. Test one CV from the terminal

```powershell
cd "C:\Users\User\Desktop\research-component-2\component 2-with frontend\backend\scripts"
python test_cv_guidance.py "..\data\cvs\CV_021_Software_Engineer.pdf" "Software Engineer"
```

Use a real file name that exists in your `data/cvs` folder.

The response should contain:

```text
cv_readiness
cv_evidence
strengths / improvements / career_paths
jobs[]
  fit
  matched_skills
  missing_skills
  apply_link
```

There is no user-facing CV score or percentage.

## 6. Optional: create a dated job-market CSV snapshot

This is useful for thesis evaluation because your live vacancies will change over time.

```powershell
cd "C:\Users\User\Desktop\research-component-2\component 2-with frontend\backend\scripts"
python fetch_google_jobs.py --roles "Software Engineer" "Frontend Developer" "Backend Developer" "QA Engineer" "Data Analyst" --location "Sri Lanka" --limit 10
```

This writes:

```text
backend/data/job_posts.csv
```

and includes `fetched_at`, so you can report exactly when the market snapshot was collected.

## 7. Add the frontend

Copy:

```text
frontend/src/services/cvGuidanceApi.js
frontend/src/components/CvGuidanceResult.jsx
frontend/src/components/CvGuidanceResult.css
frontend/src/pages/CvGuidancePage.jsx
frontend/src/pages/CvGuidancePage.css
```

Create/update frontend `.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

If your app uses React Router, add a route similar to:

```jsx
import CvGuidancePage from "./pages/CvGuidancePage";

<Route path="/cv-guidance" element={<CvGuidancePage />} />
```

If you do not use a router yet, temporarily render it from `App.jsx`:

```jsx
import CvGuidancePage from "./pages/CvGuidancePage";

export default function App() {
  return <CvGuidancePage />;
}
```

Then run your existing frontend command, normally:

```powershell
npm run dev
```

## 8. Recommended research workflow

```text
User uploads CV + selects intended job role
        |
        v
CV text extraction
        |
        +--> Existing trained ML model ----------------> CV readiness category
        |                                                Weak / Average / Good / Best
        |
        +--> Explicit CV evidence extraction ----------> skills + sections
        |
        v
SerpApi Google Jobs search for current Sri Lankan vacancies
        |
        v
Vacancy requirement extraction
        |
        v
Explainable CV-vacancy comparison
        |-- skills already evidenced
        |-- skills missing from CV evidence
        |-- categorical vacancy fit
        |
        v
Groq guidance realizer
        |-- strengths
        |-- improvements
        |-- CV maintenance advice
        |-- career paths
        |-- interview preparation
        |
        v
Frontend vacancy cards -> original public apply/view link
```

### Research separation to defend in viva

- **ML classifier:** predicts the learned CV readiness category.
- **Market evidence layer:** compares the applicant's CV with current vacancy requirements.
- **LLM:** does not assign the category and does not invent vacancies; it verbalizes grounded evidence into guidance.
- **External link:** the user makes the final choice and opens the original vacancy/application page.

## 9. Do not claim these things in your thesis

Avoid statements such as:

- “This CV has an 85% chance of passing the interview.”
- “This applicant will be hired.”
- “The system is an ATS used by employers.”

A safer and more accurate claim is:

> The prototype provides applicant-side CV readiness classification, explainable comparison against current publicly available job advertisements, and evidence-grounded career improvement guidance.

## 10. Evaluation you should add before final submission

For a strong final-year evaluation, manually verify a held-out set of CV labels and a sample of CV-vacancy matches. Report your classifier metrics separately from the job-matching evaluation. For job matching, human reviewers can mark whether the identified matched/missing skills are correct and whether the recommended vacancy is relevant to the selected role.
