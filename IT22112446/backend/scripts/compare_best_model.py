import os
import json
import joblib
import pandas as pd

MODEL_RESULTS = {
    "Logistic Regression": {
        "json": "../models/logistic_regression_result.json",
        "model": "../models/logistic_regression_model.pkl"
    },
    "Random Forest": {
        "json": "../models/random_forest_result.json",
        "model": "../models/random_forest_model.pkl"
    },
    "SVM": {
        "json": "../models/svm_result.json",
        "model": "../models/svm_model.pkl"
    }
}

BEST_MODEL_FILE = "../models/best_communication_skill_model.pkl"
BEST_MODEL_JSON_FILE = "../models/best_model_result.json"
ALL_RESULTS_JSON_FILE = "../models/all_model_results.json"
CSV_REPORT_FILE = "../models/model_comparison_report.csv"

all_results = []
best_result = None
best_model_path = None
highest_f1 = -1

print("===================================")
print("MODEL COMPARISON USING F1-SCORE")
print("===================================")

for model_name, paths in MODEL_RESULTS.items():
    json_path = paths["json"]
    model_path = paths["model"]

    if not os.path.exists(json_path):
        print(f"Missing JSON result for {model_name}: {json_path}")
        continue

    if not os.path.exists(model_path):
        print(f"Missing trained model for {model_name}: {model_path}")
        continue

    with open(json_path, "r", encoding="utf-8") as file:
        result = json.load(file)

    all_results.append(result)

    print(f"\n{model_name}")
    print("Accuracy :", result["accuracy"])
    print("Precision:", result["precision"])
    print("Recall   :", result["recall"])
    print("F1 Score :", result["f1_score"])

    if result["f1_score"] > highest_f1:
        highest_f1 = result["f1_score"]
        best_result = result
        best_model_path = model_path

if not all_results:
    print("\nNo model results found. Train models first.")
    exit()

all_results = sorted(all_results, key=lambda x: x["f1_score"], reverse=True)

with open(ALL_RESULTS_JSON_FILE, "w", encoding="utf-8") as file:
    json.dump(all_results, file, indent=4)

results_df = pd.DataFrame(all_results)
results_df.to_csv(CSV_REPORT_FILE, index=False)

if best_result is not None and best_model_path is not None:
    best_model = joblib.load(best_model_path)
    joblib.dump(best_model, BEST_MODEL_FILE)

    best_model_json = {
        "best_model": best_result["model_name"],
        "selection_metric": "highest_f1_score",
        "accuracy": best_result["accuracy"],
        "precision": best_result["precision"],
        "recall": best_result["recall"],
        "f1_score": best_result["f1_score"],
        "saved_model_path": BEST_MODEL_FILE
    }

    with open(BEST_MODEL_JSON_FILE, "w", encoding="utf-8") as file:
        json.dump(best_model_json, file, indent=4)

    print("\n===================================")
    print("MODEL COMPARISON REPORT")
    print("===================================")
    print(f"{'model_name':<25} {'accuracy':<10} {'precision':<10} {'recall':<10} {'f1_score':<10}")

    for item in all_results:
        print(
            f"{item['model_name']:<25} "
            f"{item['accuracy']:<10} "
            f"{item['precision']:<10} "
            f"{item['recall']:<10} "
            f"{item['f1_score']:<10}"
        )

    print("\n===================================")
    print("BEST MODEL SELECTED")
    print("===================================")
    print("Selection Metric: Highest F1-score")
    print("Best Model:", best_result["model_name"])
    print("Highest F1 Score:", best_result["f1_score"])
    print("Saved Best Model:", BEST_MODEL_FILE)
    print("Best Model JSON:", BEST_MODEL_JSON_FILE)
    print("All Results JSON:", ALL_RESULTS_JSON_FILE)
    print("CSV Report:", CSV_REPORT_FILE)