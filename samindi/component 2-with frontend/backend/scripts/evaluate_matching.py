\
import csv
import json
from pathlib import Path
import sys

from sklearn.metrics import precision_recall_fscore_support

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from services.skill_catalog import canonicalize_skill_names, extract_skills  # noqa: E402


DEFAULT_FILE = BASE_DIR / "evaluation" / "job_match_eval.csv"


def split_skills(value):
    if not value:
        return []
    return [x.strip() for x in value.split(";") if x.strip()]


def per_case_set_metrics(predicted, gold):
    pred = set(canonicalize_skill_names(predicted))
    gold = set(canonicalize_skill_names(gold))

    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)

    precision = tp / (tp + fp) if (tp + fp) else (1.0 if not gold else 0.0)
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    return precision, recall, f1


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE

    if not path.exists():
        raise FileNotFoundError(
            f"Evaluation file not found: {path}\n"
            "Fill backend/evaluation/job_match_eval.csv first."
        )

    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))

    if not rows:
        print("No evaluation rows.")
        return

    skill_metrics = []
    matched_metrics = []
    missing_metrics = []
    details = []

    for row in rows:
        cv_text = row.get("cv_text", "")
        job_text = row.get("job_text", "")

        cv_skills = set(extract_skills(cv_text))
        predicted_job_skills = set(extract_skills(job_text))

        predicted_matched = cv_skills & predicted_job_skills
        predicted_missing = predicted_job_skills - cv_skills

        gold_job = split_skills(row.get("gold_job_skills", ""))
        gold_matched = split_skills(row.get("gold_matched_skills", ""))
        gold_missing = split_skills(row.get("gold_missing_skills", ""))

        skill_metrics.append(per_case_set_metrics(predicted_job_skills, gold_job))
        matched_metrics.append(per_case_set_metrics(predicted_matched, gold_matched))
        missing_metrics.append(per_case_set_metrics(predicted_missing, gold_missing))

        details.append({
            "case_id": row.get("case_id"),
            "predicted_job_skills": sorted(predicted_job_skills),
            "predicted_matched": sorted(predicted_matched),
            "predicted_missing": sorted(predicted_missing),
        })

    def avg(values):
        n = len(values)
        return {
            "precision": round(sum(x[0] for x in values) / n, 4),
            "recall": round(sum(x[1] for x in values) / n, 4),
            "f1": round(sum(x[2] for x in values) / n, 4),
        }

    result = {
        "cases": len(rows),
        "job_skill_extraction_macro": avg(skill_metrics),
        "matched_skill_detection_macro": avg(matched_metrics),
        "missing_skill_detection_macro": avg(missing_metrics),
        "case_predictions": details,
    }

    output = BASE_DIR / "evaluation" / "job_match_evaluation_result.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    print(f"\nSaved: {output}")


if __name__ == "__main__":
    main()
