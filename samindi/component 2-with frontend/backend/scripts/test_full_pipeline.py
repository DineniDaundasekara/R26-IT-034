\
import json
import sys
from pathlib import Path

import requests


API_URL = "http://127.0.0.1:8000/api/analyze-cv"


def main():
    if len(sys.argv) < 3:
        print(
            'Usage: python test_full_pipeline.py "..\\data\\cvs\\CV.pdf" '
            '"Software Engineer"'
        )
        raise SystemExit(1)

    cv_path = Path(sys.argv[1])
    job_role = sys.argv[2]
    location = sys.argv[3] if len(sys.argv) >= 4 else "Sri Lanka"

    if not cv_path.exists():
        raise FileNotFoundError(cv_path)

    with cv_path.open("rb") as fh:
        response = requests.post(
            API_URL,
            files={"cv": (cv_path.name, fh)},
            data={
                "job_role": job_role,
                "location": location,
                "max_jobs": "5",
            },
            timeout=120,
        )

    print("HTTP:", response.status_code)

    try:
        payload = response.json()
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    except Exception:
        print(response.text)


if __name__ == "__main__":
    main()
