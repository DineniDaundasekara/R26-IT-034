# InterviewReady AI Communication Coach — Final Research Build

This project separates **prediction**, **evidence**, and **generative coaching** so the final-year research claim is clear and defensible.

## Final runtime architecture

```text
NEW CANDIDATE AUDIO
        ↓
Faster-Whisper
        ↓
Transcript
        ↓
NLP + Spoken-Audio Feature Builder
        ↓
Saved ML Pipeline (your selected Linear SVM)
        ↓
Poor / Average / Good / Excellent
        ↓
Deterministic Evidence Extraction
        ↓
Grounded OpenAI Coaching Layer
        ↓
Strengths + Weaknesses + Professional Rewrites
Speaking Patterns + STAR Coach + Practice Answer
7-Day Plan + Activities + Mock Interview + Follow-up Coach
        ↓
Practice Completion + Attempt History
        ↓
Fresh Candidate Recording
```

## Why this design is strong for research

1. **The ML model owns the communication category.** The OpenAI model is never asked to predict or change the category.
2. **Evidence is extracted before generative guidance.** Guidance is grounded in observable transcript evidence such as context, ownership language, actions, results, and fillers.
3. **The generative model is constrained.** It is explicitly told not to invent candidate projects, metrics, employers, technologies, or achievements.
4. **The candidate UI has no artificial communication score.** Research Accuracy/Macro-F1 stay in research files only.
5. **Progress tracking measures practice completion, not fake skill improvement.**
6. **The system remains usable without OpenAI.** If the API is unavailable, deterministic evidence-based guidance is returned.

## Important: keep your already-trained model

This source ZIP does not contain your local trained binary. Copy these files from your current working backend into:

```text
backend/models/
    communication_pipeline.joblib
    model_metadata.json
    research_metrics.json
```

Do **not** retrain just because you added the OpenAI guidance layer.

Your latest duplicate-safe research run selected **Linear SVM**.

## Backend setup — Windows PowerShell

```powershell
cd C:\sam\NLP\communication_skill\backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Edit `backend\.env`:

```text
OPENAI_GUIDANCE_ENABLED=true
OPENAI_API_KEY=YOUR_REAL_KEY_HERE
OPENAI_GUIDANCE_MODEL=gpt-5.6-sol
OPENAI_GUIDANCE_VERIFY=true
OPENAI_VERIFIER_MODEL=gpt-5.6-sol
```

**Never put the OpenAI key in React/Vite code. Never commit `.env`.**

Start backend:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Check:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

Expected health response when everything is configured:

```json
{
  "success": true,
  "modelReady": true,
  "aiGuidanceReady": true,
  "aiGuidanceModel": "gpt-5.6-sol"
}
```

## Frontend setup

```powershell
cd C:\sam\NLP\communication_skill\frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Advanced candidate experience

The UI contains:

- target-role and practice-goal context
- live microphone recording
- audio upload
- model category
- Whisper transcript
- "what you already demonstrate" knowledge snapshot
- "what to build next" knowledge snapshot
- top 3 communication priorities
- evidence-grounded strengths and weaknesses
- professional English rewrite lab
- reusable spoken-English sentence patterns
- personalised practice answer
- browser text-to-speech for the practice answer
- personalised STAR coach
- next-attempt challenge
- practice activities with completion checks
- seven-day communication sprint
- practice completion bar
- practice-day streak and practice milestones
- tailored mock interview questions
- OpenAI follow-up coach
- attempt history showing model categories and focus areas over time

## Training reproduction workflow

Only use this when you intentionally need to reproduce/retrain the research model.

```text
00_extract_audio_zip.py
        ↓
02_transcribe_training_audio.py
        ↓
02b_auto_label_transcripts.py      OPTIONAL provisional helper
        ↓
Human/expert review of labels
        ↓
02c_prepare_final_labels.py         if using provisional sheet
        ↓
01_validate_dataset.py
        ↓
03_build_training_features.py
        ↓
04_train_models.py
        ↓
05_test_saved_model.py
```

Example commands:

```powershell
python -m training.02_transcribe_training_audio
python -m training.02b_auto_label_transcripts
python -m training.02c_prepare_final_labels
python -m training.01_validate_dataset
python -m training.03_build_training_features
python -m training.04_train_models
python -m training.05_test_saved_model "C:\path\to\new_test.wav" "QA Engineer"
```

Automatic labels must be described as **rubric-based provisional labels**, not ground truth.

## Candidate-facing output policy

Allowed:

```text
Average Communication
Strengths
Areas to improve
Professional English guidance
STAR guidance
Practice answer
Activities
Practice completion
Mock interview prompts
```

Do not show:

```text
Model confidence
Communication percentage
Clarity percentage
Professionalism percentage
Speaking-rate score
Silence score
Raw ML feature values
Research Accuracy/Macro-F1
```

## Research result reference from the latest duplicate-safe run

See `docs/FINAL_RESEARCH_RESULTS.md`.
