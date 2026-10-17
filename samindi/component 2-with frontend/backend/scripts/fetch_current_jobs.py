import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv  # noqa: E402
from services.job_search_service import JobSearchService  # noqa: E402

load_dotenv(BASE_DIR / ".env")


def main():
    role = sys.argv[1] if len(sys.argv) > 1 else "Software Engineer"
    location = sys.argv[2] if len(sys.argv) > 2 else "Sri Lanka"

    service = JobSearchService()
    result = service.search_all_sources(role, location, google_limit=5, topjobs_limit=5)

    summary = {
        "role": role,
        "location": location,
        "google_jobs_count": len(result["google_jobs"]),
        "topjobs_count": len(result["topjobs_jobs"]),
        "errors": result["errors"],
        "jobs": result["all_jobs"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
