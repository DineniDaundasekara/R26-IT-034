\
import csv
import json
import statistics
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_FILE = BASE_DIR / "evaluation" / "guidance_human_eval.csv"

CRITERIA = [
    "evidence_faithfulness",
    "relevance",
    "actionability",
    "clarity",
    "no_fabrication",
]


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE

    if not path.exists():
        raise FileNotFoundError(path)

    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))

    valid_rows = []
    for row in rows:
        try:
            values = {c: float(row[c]) for c in CRITERIA}
        except (KeyError, TypeError, ValueError):
            continue

        if all(1 <= v <= 5 for v in values.values()):
            valid_rows.append(values)

    if not valid_rows:
        print("No valid 1-5 evaluation rows found.")
        return

    result = {
        "valid_ratings": len(valid_rows),
        "scale": "1-5",
        "criteria": {},
    }

    for criterion in CRITERIA:
        values = [row[criterion] for row in valid_rows]
        result["criteria"][criterion] = {
            "mean": round(statistics.mean(values), 3),
            "median": round(statistics.median(values), 3),
            "min": min(values),
            "max": max(values),
        }

    output = BASE_DIR / "evaluation" / "guidance_human_evaluation_result.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    print(f"\nSaved: {output}")


if __name__ == "__main__":
    main()
