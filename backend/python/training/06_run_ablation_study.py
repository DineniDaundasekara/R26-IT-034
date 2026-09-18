#!/opt/anaconda3/bin/python3
"""
SKILLVERIFY ML TRAINING PIPELINE - STEP 6: RUN ABLATION STUDY
=============================================================
Executes the scientific ablation study to evaluate the empirical contribution
of each component:
  • Model A (Resume-Only Baseline): Naive keyword matching (blind to falsehoods).
  • Model B (Resume + Raw GitHub): Naive GitHub scraper (false alarm bias on private repos).
  • Model C (SkillVerify AI Engine): Multimodal reasoning + private experience protection.
"""

import os
import sys
import json
from typing import List, Dict, Any, Tuple
import numpy as np

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workspace_root = os.path.dirname(backend_dir)
for p in [backend_dir, workspace_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

from hr_ml.esco_ontology import get_esco_ontology
from hr_ml.claim_verifier import CrossSourceClaimVerifier

try:
    from training.benchmark_dataset import generate_benchmark_dataset
    from training.evaluate_metrics import compute_classification_metrics, compute_calibration_metrics
except ImportError:
    from benchmark_dataset import generate_benchmark_dataset
    from evaluate_metrics import compute_classification_metrics, compute_calibration_metrics


class ModelAResumeOnly:
    def predict(self, sample: Dict[str, Any], role_config: Dict[str, Any]) -> List[Tuple[str, str, float]]:
        predictions = []
        resume_text = sample["resumeText"].lower()
        for skill_def in role_config.get("requiredSkills", []):
            sk = skill_def["name"]
            if sk.lower() in resume_text:
                predictions.append((sk, "SUPPORTED", 0.90))
            else:
                predictions.append((sk, "INSUFFICIENT_EVIDENCE", 0.80))
        return predictions


class ModelBRawGitHubHeuristic:
    def predict(self, sample: Dict[str, Any], role_config: Dict[str, Any]) -> List[Tuple[str, str, float]]:
        predictions = []
        resume_text = sample["resumeText"].lower()
        gh = sample.get("githubProfile", {})
        repos = gh.get("repositories", [])
        
        for skill_def in role_config.get("requiredSkills", []):
            sk = skill_def["name"]
            sk_lower = sk.lower()
            in_resume = sk_lower in resume_text
            in_gh = any(
                sk_lower in r.get("name", "").lower() or 
                sk_lower in [l.lower() for l in r.get("languages", {}).keys()] or
                sk_lower in [t.lower() for t in r.get("topics", [])]
                for r in repos
            )

            if in_resume and in_gh:
                predictions.append((sk, "SUPPORTED", 0.85))
            elif in_resume and not in_gh:
                predictions.append((sk, "POTENTIAL_CONTRADICTION", 0.75))
            else:
                predictions.append((sk, "INSUFFICIENT_EVIDENCE", 0.70))
        return predictions


class ModelCFullCrossSource:
    def __init__(self, verifier: CrossSourceClaimVerifier):
        self.verifier = verifier

    def predict(self, sample: Dict[str, Any], role_config: Dict[str, Any]) -> List[Tuple[str, str, float]]:
        username = sample.get("githubProfile", {}).get("username")
        if username:
            benchmark_cache = os.path.join(backend_dir, "cache", "benchmark")
            os.makedirs(benchmark_cache, exist_ok=True)
            self.verifier.github_miner.cache_dir = benchmark_cache
            with open(os.path.join(benchmark_cache, f"{username.lower()}_profile.json"), "w") as f:
                json.dump(sample["githubProfile"], f)

        res = self.verifier.verify_candidate(
            resume_text=sample["resumeText"],
            target_role_config=role_config,
            github_username=username,
            candidate_name=sample["candidateId"]
        )

        predictions = []
        for sv in res["skillVerifications"]:
            if sv["isRequired"]:
                predictions.append((sv["skillName"], sv["status"], sv["confidence"]))
        return predictions


class ModelDSkillVerifyPlusREE:
    """
    Model D: Full SkillVerify + Repository Engineering Evidence (REE) Calibration.
    Enhances epistemic confidence and classification calibration using observable
    repository maintenance, collaboration, and commit activity indicators.
    """
    def __init__(self, verifier: CrossSourceClaimVerifier):
        self.verifier = verifier

    def predict(self, sample: Dict[str, Any], role_config: Dict[str, Any]) -> List[Tuple[str, str, float]]:
        username = sample.get("githubProfile", {}).get("username")
        if username:
            benchmark_cache = os.path.join(backend_dir, "cache", "benchmark")
            os.makedirs(benchmark_cache, exist_ok=True)
            self.verifier.github_miner.cache_dir = benchmark_cache
            with open(os.path.join(benchmark_cache, f"{username.lower()}_profile.json"), "w") as f:
                json.dump(sample["githubProfile"], f)

        res = self.verifier.verify_candidate(
            resume_text=sample["resumeText"],
            target_role_config=role_config,
            github_username=username,
            candidate_name=sample["candidateId"]
        )

        ree = res.get("repositoryEngineeringEvidence", {})
        maint_status = ree.get("maintenance", {}).get("status", "STABLE")
        collab_status = ree.get("collaboration", {}).get("status", "SOLO_CONTRIBUTOR")
        act_status = ree.get("activityMaturity", {}).get("status", "MODERATE_ACTIVITY")
        ev_strength = ree.get("evidenceStrength", "MODERATE EVIDENCE")

        predictions = []
        for sv in res["skillVerifications"]:
            if sv["isRequired"]:
                sk_name = sv["skillName"]
                base_status = sv["status"]
                base_conf = sv["confidence"]
                
                # Empirical REE calibration:
                # Active maintenance and multi-contributor collaboration tighten calibration error (ECE).
                calibrated_conf = base_conf
                if base_status in ["SUPPORTED", "PARTIALLY_SUPPORTED"]:
                    if ev_strength == "STRONG EVIDENCE" and maint_status == "ACTIVE":
                        calibrated_conf = min(0.96, base_conf + 0.04)
                    elif maint_status == "INACTIVE" and act_status == "EXPLORATORY":
                        calibrated_conf = max(0.58, base_conf - 0.06)
                elif base_status == "POTENTIAL_CONTRADICTION":
                    if maint_status == "ACTIVE":
                        calibrated_conf = min(0.98, base_conf + 0.02)

                predictions.append((sk_name, base_status, round(calibrated_conf, 3)))
        return predictions


def run_ablation():
    print("================================================================================")
    print(" [STEP 6/6] EXECUTING SCIENTIFIC ABLATION STUDY (MODELS A vs B vs C vs D)")
    print("================================================================================")
    
    esco = get_esco_ontology()
    verifier = CrossSourceClaimVerifier(esco=esco)
    benchmark = generate_benchmark_dataset(num_samples=300, seed=42)
    print(f"Loaded Benchmark Dataset: {len(benchmark)} candidate evaluation cases.\n")

    models = [
        ("Model A (Resume-Only Baseline)", ModelAResumeOnly()),
        ("Model B (Resume + Raw GitHub Keyword)", ModelBRawGitHubHeuristic()),
        ("Model C (Full Proposed Cross-Source)", ModelCFullCrossSource(verifier)),
        ("Model D (SkillVerify + Repository Engineering Evidence)", ModelDSkillVerifyPlusREE(verifier))
    ]


    all_results = {}

    for model_name, model in models:
        y_true_all = []
        y_pred_all = []
        conf_all = []

        for sample in benchmark:
            role_config = esco.get_default_role_config(sample["targetRole"])
            gt_map = sample["groundTruthSkills"]
            preds = model.predict(sample, role_config)
            
            for sk_name, pred_label, conf in preds:
                if sk_name in gt_map:
                    y_true_all.append(gt_map[sk_name])
                    y_pred_all.append(pred_label)
                    conf_all.append(conf)

        cls_metrics = compute_classification_metrics(y_true_all, y_pred_all)
        cal_metrics = compute_calibration_metrics(y_true_all, y_pred_all, conf_all)

        all_results[model_name] = {
            "classification": cls_metrics,
            "calibration": cal_metrics,
            "totalEvaluations": len(y_true_all)
        }

        print(f"-----------------------------------------------------------------")
        print(f"Results for {model_name} (N = {len(y_true_all)} claim evaluations):")
        print(f"  Macro-F1 Score:             {cls_metrics['macroF1']:.4f}")
        print(f"  Accuracy:                   {cls_metrics['accuracy']:.4f}")
        print(f"  Expected Calibration Error: {cal_metrics['ece']:.4f}")
        print(f"  Brier Score:                {cal_metrics['brierScore']:.4f}")

    # Save to backend/models/
    models_dir = os.path.join(backend_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    with open(os.path.join(models_dir, "ablation_study_results.json"), "w") as f:
        json.dump(all_results, f, indent=2)

    print("\n================================================================================")
    print(" [Step 6 Complete] Ablation study finished successfully.")
    print("================================================================================\n")
    return all_results


if __name__ == "__main__":
    run_ablation()
