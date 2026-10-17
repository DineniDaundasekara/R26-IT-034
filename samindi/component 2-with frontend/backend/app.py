from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from services.career_path_model_service import CareerPathModelService
from services.cv_reader import build_cv_evidence, extract_cv_text
from services.guidance_service import GuidanceService
from services.job_match_service import compare_cv_to_jobs
from services.job_search_service import JobSearchService
from services.readiness_service import ReadinessService


BACKEND_DIR = Path(__file__).resolve().parent

load_dotenv(BACKEND_DIR / ".env")


app = FastAPI(
    title="CareerLens CV Guidance API",
    version="3.1.0",
    description=(
        "Career-path classification, deterministic CV evidence extraction, "
        "Google Jobs, TopJobs and LinkedIn Jobs retrieval, "
        "explainable skill-gap matching and grounded career guidance."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5180",
        "http://127.0.0.1:5180",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



career_model = CareerPathModelService(BACKEND_DIR)
try:
    career_model.load()
except Exception as exc:
    print("WARNING: career path model did not load at startup:", exc)

readiness_service = ReadinessService()



@app.get("/")
def root():

    return {

        "status":"ok",

        "message":
        "CareerLens CV Guidance API running",

        "version":"3.1.0",

        "endpoints":{

            "health":"/health",

            "jobs":"/api/jobs",

            "analyze_cv":"/api/analyze-cv"

        }

    }




@app.get("/health")
def health():

    jobs = JobSearchService()

    guidance = GuidanceService()


    return {

        "status":"ok",

        "career_path_model_exists":
            career_model.exists(),

        "serpapi_configured":
            jobs.configured(),

        "groq_configured":
            guidance.configured(),

        "groq_model":
            guidance.model

    }




def validate_search(job_role, location, limit):

    job_role = (job_role or "").strip()

    location = (
        location or "Sri Lanka"
    ).strip()


    if not job_role:

        raise HTTPException(
            status_code=400,
            detail="Job role required"
        )


    if limit < 1 or limit > 10:

        raise HTTPException(
            status_code=400,
            detail="Limit should be between 1 and 10"
        )


    return job_role, location





# ======================================================
# ALL JOB SOURCES API
# ======================================================


@app.get("/api/jobs")
def get_jobs(

    job_role:str,

    location:str="Sri Lanka",

    limit:int=5

):


    job_role,location = validate_search(
        job_role,
        location,
        limit
    )


    service = JobSearchService()


    result = service.search_all_sources(

        job_role=job_role,

        location=location,

        google_limit=limit,

        topjobs_limit=min(limit,5),

        linkedin_limit=min(limit,5)

    )



    return {


        "status":"success",

        "job_role":job_role,

        "location":location,


        "google_jobs":
            result["google_jobs"],


        "topjobs_jobs":
            result["topjobs_jobs"],


        "linkedin_jobs":
            result["linkedin_jobs"],


        "jobs":
            result["all_jobs"],


        "errors":
            result["errors"]

    }





# ======================================================
# CV ANALYSIS API
# ======================================================


@app.post("/api/analyze-cv")
async def analyze_cv(


    cv:UploadFile = File(...),


    job_role:str = Form(...),


    location:str = Form("Sri Lanka"),


    max_jobs:int = Form(5)


):


    try:


        job_role = job_role.strip()


        location = (
            location.strip()
            if location
            else "Sri Lanka"
        )



        if not job_role:


            raise ValueError(
                "Please select job role"
            )



        print("STEP 1 : Reading CV")



        data = await cv.read()



        if not data:

            raise ValueError(
                "Empty CV uploaded"
            )



        filename = cv.filename or "cv.pdf"



        cv_text = extract_cv_text(

            filename,

            data

        )



        print("STEP 2 : CV extracted")



        if len(cv_text.strip()) < 80:


            raise ValueError(
                "Unable to extract CV text"
            )




        # --------------------------------
        # CV evidence extraction
        # --------------------------------


        cv_evidence = build_cv_evidence(
            cv_text
        )



        print(
            "STEP 3 : Evidence completed"
        )





        # --------------------------------
        # Career prediction
        # --------------------------------


        predicted_career_path = career_model.predict(
            cv_text
        )



        print(
            "STEP 4 : Career model completed"
        )





        # --------------------------------
        # Job retrieval
        # --------------------------------


        search_service = JobSearchService()



        jobs_result = search_service.search_all_sources(

            job_role=job_role,

            location=location,

            google_limit=max_jobs,

            topjobs_limit=min(max_jobs,5),

            linkedin_limit=min(max_jobs,5)

        )



        print(
            "STEP 5 : Jobs retrieved"
        )





        # --------------------------------
        # Skill matching
        # --------------------------------


        compared_jobs = compare_cv_to_jobs(

            cv_skills=
            cv_evidence.get(
                "skills",
                []
            ),


            target_role=
            job_role,


            jobs=
            jobs_result["all_jobs"]

        )



        print(
            "STEP 6 : Matching completed"
        )





        # --------------------------------
        # CV readiness
        # --------------------------------


        readiness = readiness_service.assess(
            cv_evidence=cv_evidence,
            matched_jobs=compared_jobs,
            target_role=job_role,
            predicted_career_path=predicted_career_path,
        )





        # --------------------------------
        # AI guidance
        # --------------------------------


        guidance = GuidanceService().generate(

            target_role=job_role,


            predicted_career_path=
            predicted_career_path,


            cv_evidence=cv_evidence,


            readiness=readiness,


            jobs=compared_jobs

        )



        print(
            "STEP 7 : Guidance completed"
        )





        return {


            "status":"success",


            "target_role":
                job_role,


            "location":
                location,



            "career_path_prediction":{


                "label":
                    predicted_career_path,


                "method":
                    "trained_supervised_nlp_pipeline",


                "model":
                    career_model.metadata()

            },



            "cv_readiness":
                readiness,



            "cv_evidence":
                cv_evidence,



            "guidance":
                guidance,



            # all recommended jobs
            "jobs":
                compared_jobs,



            # separated source lists
            "google_jobs":
                [
                    j for j in compared_jobs
                    if j.get("source_type")
                    =="google_jobs"
                ],



            "topjobs_jobs":
                [
                    j for j in compared_jobs
                    if j.get("source_type")
                    =="topjobs"
                ],



            "linkedin_jobs":
                [
                    j for j in compared_jobs
                    if j.get("source_type")
                    =="linkedin_jobs"
                ],



            "methodology":{


                "career_path":
                    "Trained CV text classification model",


                "cv_evidence":
                    "Deterministic CV extraction",


                "vacancies":
                    "Google Jobs + TopJobs + LinkedIn Jobs",


                "matching":
                    "Explainable skill evidence comparison",


                "guidance":
                    "Grounded AI career guidance",


                "numeric_score":
                    False

            }

        }




    except Exception as exc:


        print(
            "ERROR:",
            exc
        )


        raise HTTPException(

            status_code=400,

            detail=str(exc)

        )