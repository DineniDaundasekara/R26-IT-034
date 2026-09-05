#!/opt/anaconda3/bin/python3
"""
SKILLVERIFY ML MASTER TRAINING ORCHESTRATOR
===========================================
Runs the complete research training pipeline in sequence:
  Step 1: 01_validate_raw_datasets.py
  Step 2: 02_preprocess_and_clean_data.py
  Step 3: 03_build_training_features.py
  Step 4: 04_train_models.py
  Step 5: 05_evaluate_and_select_best_model.py
  Step 6: 06_run_ablation_study.py
"""

import os
import sys
import subprocess

training_dir = os.path.dirname(os.path.abspath(__file__))
python_bin = sys.executable

STEPS = [
    ("Step 1: Dataset Integrity Audit", "01_validate_raw_datasets.py"),
    ("Step 2: Data Preprocessing & Cleaning", "02_preprocess_and_clean_data.py"),
    ("Step 3: Multimodal Feature Engineering", "03_build_training_features.py"),
    ("Step 4: 5-Fold Stratified CV & Model Training", "04_train_models.py"),
    ("Step 5: Test Benchmark Evaluation & Selection", "05_evaluate_and_select_best_model.py"),
    ("Step 6: Scientific Ablation Study", "06_run_ablation_study.py")
]


def run_full_pipeline():
    print("################################################################################")
    print("       SKILLVERIFY: COMPLETE END-TO-END MACHINE LEARNING RESEARCH PIPELINE     ")
    print("################################################################################\n")

    for step_title, script_name in STEPS:
        script_path = os.path.join(training_dir, script_name)
        if not os.path.exists(script_path):
            print(f"Error: Missing script {script_path}")
            sys.exit(1)

        cmd = [python_bin, script_path]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"\n[PIPELINE FAILED] Error during {step_title} ({script_name}).")
            sys.exit(res.returncode)

    print("################################################################################")
    print("       ALL 6 PHASES COMPLETED WITH 100% SUCCESS! MODEL ARTEFACTS READY!        ")
    print("################################################################################\n")


if __name__ == "__main__":
    run_full_pipeline()
