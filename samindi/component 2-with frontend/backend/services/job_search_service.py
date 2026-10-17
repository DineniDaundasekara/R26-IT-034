import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
from urllib.parse import quote_plus, urlparse

import requests

JOB_SEARCH_TIMEOUT = 15


SERPAPI_URL = "https://serpapi.com/search.json"
TOPJOBS_PORTAL_URL = "https://www.topjobs.lk/"


def _serpapi_get(params):
    """GET SerpAPI with one retry, so a single slow/flaky response doesn't
    wipe out an entire source's results in the live search."""
    last_error = None
    for attempt in range(2):
        try:
            response = requests.get(SERPAPI_URL, params=params, timeout=JOB_SEARCH_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = exc
    raise last_error


class JobSearchService:

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY", "").strip()


    def configured(self):
        return bool(self.api_key)



    @staticmethod
    def _dedupe_jobs(jobs):

        result = []
        seen = set()

        for job in jobs:

            key = (
                job.get("title",""),
                job.get("company",""),
                job.get("primary_apply_url","")
            )

            if key not in seen:
                seen.add(key)
                result.append(job)

        return result



    @staticmethod
    def _is_topjobs_url(url):

        try:
            host=urlparse(url).netloc.lower()
            return (
                host=="topjobs.lk"
                or host.endswith(".topjobs.lk")
            )

        except:
            return False




    def search_google_jobs(
        self,
        job_role,
        location="Sri Lanka",
        limit=5
    ):

        if not self.api_key:
            return []


        params={
            "engine":"google_jobs",
            "q":f"{job_role} jobs",
            "location":location,
            "hl":"en",
            "gl":"lk",
            "api_key":self.api_key
        }


        data = _serpapi_get(params)


        jobs=[]


        for item in data.get("jobs_results",[])[:limit]:

            apply_url=""

            if item.get("apply_options"):
                apply_url=item["apply_options"][0].get("link","")


            jobs.append({

                "title":item.get("title"),
                "company":item.get("company_name"),
                "location":item.get("location"),

                "description":
                    item.get("description",""),

                "share_link":
                    item.get("share_link",""),

                "primary_apply_url":
                    apply_url,

                "apply_options":
                    item.get("apply_options",[]),

                "source_type":
                    "google_jobs",

                "source_name":
                    "Google Jobs"

            })


        return jobs





    def search_topjobs_jobs(
        self,
        job_role,
        location="Sri Lanka",
        limit=5
    ):


        if not self.api_key:
            return []


        query=f'site:topjobs.lk "{job_role}" "{location}"'


        params={

            "engine":"google",
            "q":query,
            "hl":"en",
            "gl":"lk",
            "num":10,
            "api_key":self.api_key

        }


        data = _serpapi_get(params)


        jobs=[]


        for item in data.get("organic_results",[]):

            link=item.get("link","")


            if not self._is_topjobs_url(link):
                continue


            jobs.append({

                "title":
                    item.get("title",job_role),

                "company":
                    "TopJobs",

                "location":
                    location,


                "description":
                    item.get("snippet",""),


                "primary_apply_url":
                    link,


                "share_link":
                    link,


                "apply_options":[
                    {
                        "source":"TopJobs",
                        "url":link
                    }
                ],


                "source_type":
                    "topjobs",


                "source_name":
                    "TopJobs"

            })


            if len(jobs)>=limit:
                break



        return jobs






    def search_linkedin_jobs(
        self,
        job_role,
        location="Sri Lanka",
        limit=5
    ):


        if not self.api_key:
            return []



        query=f'site:linkedin.com/jobs "{job_role}" "{location}"'


        params={

            "engine":"google",
            "q":query,
            "hl":"en",
            "gl":"lk",
            "num":10,
            "api_key":self.api_key

        }



        data = _serpapi_get(params)


        jobs=[]


        for item in data.get("organic_results",[]):

            link=item.get("link","")


            if "linkedin.com/jobs" not in link.lower():
                continue



            jobs.append({

                "title":
                    item.get("title",job_role),


                "company":
                    "LinkedIn Jobs",


                "location":
                    location,


                "description":
                    item.get("snippet",""),


                "primary_apply_url":
                    link,


                "share_link":
                    link,


                "apply_options":[
                    {
                        "source":"LinkedIn Jobs",
                        "url":link
                    }
                ],


                "source_type":
                    "linkedin_jobs",


                "source_name":
                    "LinkedIn Jobs"

            })


            if len(jobs)>=limit:
                break



        return jobs






    def topjobs_search_url(
        self,
        job_role,
        location="Sri Lanka"
    ):

        query=f'site:topjobs.lk "{job_role}" "{location}"'

        return (
            "https://www.google.com/search?q="
            + quote_plus(query)
        )






    def search_all_sources(
        self,
        job_role,
        location="Sri Lanka",
        google_limit=5,
        topjobs_limit=5,
        linkedin_limit=5
    ):


        google_jobs=[]
        topjobs_jobs=[]
        linkedin_jobs=[]

        errors={}
        results = {}

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {
                pool.submit(self.search_google_jobs, job_role, location, google_limit): "google_jobs",
                pool.submit(self.search_topjobs_jobs, job_role, location, topjobs_limit): "topjobs",
                pool.submit(self.search_linkedin_jobs, job_role, location, linkedin_limit): "linkedin_jobs",
            }
            try:
                for future in as_completed(futures, timeout=JOB_SEARCH_TIMEOUT + 5):
                    key = futures[future]
                    try:
                        results[key] = future.result()
                    except Exception as e:
                        errors[key] = str(e)
            except TimeoutError:
                errors["timeout"] = "Job search exceeded the time limit"

        google_jobs = results.get("google_jobs") or []
        topjobs_jobs = results.get("topjobs") or []
        linkedin_jobs = results.get("linkedin_jobs") or []

        all_jobs=self._dedupe_jobs(
            google_jobs+
            topjobs_jobs+
            linkedin_jobs
        )

        if not all_jobs:
            fallback_jobs = self._load_fallback_dataset(
                job_role=job_role,
                location=location,
                limit=google_limit + topjobs_limit
            )
            all_jobs = fallback_jobs
            if not google_jobs and fallback_jobs:
                google_jobs = [j for j in fallback_jobs if j.get("source_type") == "google_jobs"]
            if not topjobs_jobs and fallback_jobs:
                topjobs_jobs = [j for j in fallback_jobs if j.get("source_type") != "google_jobs"]

        return {

            "google_jobs":
                google_jobs,


            "topjobs_jobs":
                topjobs_jobs,


            "linkedin_jobs":
                linkedin_jobs,


            "all_jobs":
                all_jobs,


            "errors":
                errors,


            "topjobs_portal_url":
                TOPJOBS_PORTAL_URL,


            "topjobs_search_url":
                self.topjobs_search_url(
                    job_role,
                    location
                )
        }

    @staticmethod
    def _load_fallback_dataset(job_role: str, location: str = "Sri Lanka", limit: int = 6) -> List[Dict]:
        import csv
        from pathlib import Path

        csv_path = Path(__file__).resolve().parents[1] / "data" / "job_posts.csv"
        if not csv_path.exists():
            return []

        role_lower = (job_role or "").strip().lower()
        matched = []
        other = []

        try:
            with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    item_role = (row.get("job_role") or "").strip().lower()
                    item_title = (row.get("job_title") or "").strip().lower()

                    job = {
                        "title": row.get("job_title") or job_role,
                        "company": row.get("company") or "Tech Employer",
                        "location": row.get("location") or location,
                        "description": row.get("job_description") or (row.get("required_skills") or ""),
                        "share_link": row.get("source_url") or "https://www.topjobs.lk/",
                        "primary_apply_url": row.get("source_url") or "https://www.topjobs.lk/",
                        "apply_options": [{"source": "Curated Vacancy", "url": row.get("source_url") or "https://www.topjobs.lk/"}],
                        "source_type": "google_jobs" if "google" in (row.get("data_source") or "").lower() else "topjobs",
                        "source_name": "Curated Market Vacancies",
                        "required_skills": [s.strip() for s in (row.get("required_skills") or "").split(",") if s.strip()],
                    }

                    if role_lower in item_role or role_lower in item_title or item_role in role_lower:
                        matched.append(job)
                    else:
                        other.append(job)

            result = matched[:limit]
            if len(result) < limit:
                result.extend(other[: limit - len(result)])
            return result
        except Exception:
            return []