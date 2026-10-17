import os
import json
import shutil
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_FOLDER = os.path.join(BASE_DIR, "models")

RESULT_FILES = {
    "Logistic Regression": os.path.join(MODEL_FOLDER, "logistic_regression_cv_result.json"),
    "Random Forest": os.path.join(MODEL_FOLDER, "random_forest_cv_result.json"),
    "SVM": os.path.join(MODEL_FOLDER, "svm_cv_result.json")
}

MODEL_FILES = {
    "Logistic Regression": os.path.join(MODEL_FOLDER, "logistic_regression_cv_model.pkl"),
    "Random Forest": os.path.join(MODEL_FOLDER, "random_forest_cv_model.pkl"),
    "SVM": os.path.join(MODEL_FOLDER, "svm_cv_model.pkl")
}

BEST_MODEL_FILE = os.path.join(MODEL_FOLDER, "best_cv_guidance_model.pkl")
BEST_RESULT_FILE = os.path.join(MODEL_FOLDER, "best_cv_model_result.json")
ALL_RESULTS_FILE = os.path.join(MODEL_FOLDER, "all_cv_model_results.json")
CSV_REPORT_FILE = os.path.join(MODEL_FOLDER, "cv_model_comparison_report.csv")


def main():
    print("===================================")
    print("CV MODEL COMPARISON")
    print("===================================")

    results = []

    for model_name, result_file in RESULT_FILES.items():
        if not os.path.exists(result_file):
            print("Missing result file:", result_file)
            continue

        with open(result_file, "r", encoding="utf-8") as file:
            result = json.load(file)

        results.append({
            "model_name": model_name,
            "accuracy": result["accuracy"],
            "precision": result["precision"],
            "recall": result["recall"],
            "f1_score": result["f1_score"]
        })

    if not results:
        print("No model results found. Train all models first.")
        return

    df = pd.DataFrame(results)
    df = df.sort_values("f1_score", ascending=False)

    best_row = df.iloc[0]
    best_model_name = best_row["model_name"]

    if not os.path.exists(MODEL_FILES[best_model_name]):
        print("Best model file missing:", MODEL_FILES[best_model_name])
        return

    shutil.copyfile(MODEL_FILES[best_model_name], BEST_MODEL_FILE)

    best_result = {
        "best_model": best_model_name,
        "selection_metric": "highest_f1_score",
        "accuracy": float(best_row["accuracy"]),
        "precision": float(best_row["precision"]),
        "recall": float(best_row["recall"]),
        "f1_score": float(best_row["f1_score"]),
        "saved_model_path": BEST_MODEL_FILE,
        "explanation": "The best CV career guidance model was selected using the highest F1-score from Logistic Regression, Random Forest, and SVM."
    }

    with open(BEST_RESULT_FILE, "w", encoding="utf-8") as file:
        json.dump(best_result, file, indent=4)

    with open(ALL_RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)

    df.to_csv(CSV_REPORT_FILE, index=False)

    print(f"{'model_name':<25} {'accuracy':<10} {'precision':<10} {'recall':<10} {'f1_score':<10}")

    for _, row in df.iterrows():
        print(
            f"{row['model_name']:<25} "
            f"{row['accuracy']:<10} "
            f"{row['precision']:<10} "
            f"{row['recall']:<10} "
            f"{row['f1_score']:<10}"
        )

    print("\n===================================")
    print("BEST MODEL SELECTED")
    print("===================================")
    print("Best Model:", best_model_name)
    print("Selection Metric: Highest F1-score")
    print("Best F1-score:", best_row["f1_score"])
    print("Saved Best Model:", BEST_MODEL_FILE)
    print("Best Result JSON:", BEST_RESULT_FILE)
    print("All Results JSON:", ALL_RESULTS_FILE)
    print("CSV Report:", CSV_REPORT_FILE)


if __name__ == "__main__":
    main()