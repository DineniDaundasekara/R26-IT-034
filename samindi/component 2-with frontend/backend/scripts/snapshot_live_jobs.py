\
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv  # noqa: E402
from services.job_search_service import JobSearchService  # noqa: E402

load_dotenv(BASE_DIR / ".env")


def main():
    if len(sys.argv) < 2:
        print('Usage: python snapshot_live_jobs.py "Software Engineer" "Sri Lanka"')
        raise SystemExit(1)

    job_role = sys.argv[1]
    location = sys.argv[2] if len(sys.argv) >= 3 else "Sri Lanka"

    service = JobSearchService()
    jobs = service.search_google_jobs(job_role, location, 10)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_role = "".join(c if c.isalnum() else "_" for c in job_role).strip("_")
    output_dir = BASE_DIR / "outputs" / "job_snapshots"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{safe_role}_{stamp}.csv"

    fields = [
        "fetched_at_utc",
        "job_id",
        "title",
        "company",
        "location",
        "via",
        "posted_at",
        "schedule_type",
        "description",
        "qualifications",
        "responsibilities",
        "share_link",
        "primary_apply_url",
        "data_source",
    ]

    with output.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()

        for job in jobs:
            row = {k: job.get(k) for k in fields if k != "fetched_at_utc"}
            row["fetched_at_utc"] = datetime.now(timezone.utc).isoformat()
            row["qualifications"] = " | ".join(job.get("qualifications") or [])
            row["responsibilities"] = " | ".join(job.get("responsibilities") or [])
            writer.writerow(row)

    print(f"Saved {len(jobs)} jobs to:")
    print(output)


if __name__ == "__main__":
    main()
