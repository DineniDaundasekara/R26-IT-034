# CareerLens Professional Frontend

This version removes the viva-only, API-status and research-architecture panels and presents the component as a normal professional website.

## User-facing sections

- Professional landing page
- CV upload + intended role + location
- Career-path recommendation
- CV readiness level: Weak / Average / Good / Excellent
- Detected skills and CV section checklist
- CV strengths and priority improvements
- Professional CV maintenance guidance
- Career directions and interview preparation
- Recommended current vacancies
- Separate Google Jobs and TopJobs tabs
- Matched skills and skills to strengthen
- Direct public vacancy/application links

## Run

Create `.env`:

```env
VITE_CV_API_URL=http://127.0.0.1:8000
```

Then:

```powershell
npm install
npm run dev
```

Open:

http://127.0.0.1:5173

Start the FastAPI backend on port 8000 before analyzing a CV.
