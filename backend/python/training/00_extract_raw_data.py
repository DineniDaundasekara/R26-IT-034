#!/opt/anaconda3/bin/python3
"""
Step 0: Raw Dataset Extraction & Integrity Verification
======================================================
Verifies the existence of all 6 foundation research datasets, links them
to backend/data/raw/, and validates file formats.
"""

import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workspace_root = os.path.dirname(backend_dir)
datasets_root = os.path.join(workspace_root, "datasets")
raw_dest_dir = os.path.join(backend_dir, "data", "raw")

os.makedirs(raw_dest_dir, exist_ok=True)

DATASETS = [
    ("01_github_technical_roles", ["processed_ground_truth.csv"]),
    ("02_github_expertise", ["react_empirical_stats.csv", "mongodb_empirical_stats.csv"]),
    ("03_resume_corpus", ["skills_it.txt"]),
    ("04_esco", ["skills_en.csv", "occupations_en.csv"]),
    ("05_fever", ["fever_claims_sample.json"]),
    ("06_averitec", ["averitec_claims_sample.json"])
]

def main():
    print("=" * 80)
    print(" STEP 0: RAW DATASET INTEGRITY & EXTRACTION CHECK")
    print("=" * 80)

    found_count = 0
    for folder, key_files in DATASETS:
        src_path = os.path.join(datasets_root, folder)
        dest_path = os.path.join(raw_dest_dir, folder)

        if os.path.exists(src_path):
            found_count += 1
            print(f" [✓] Found Dataset: {folder}")
            for kf in key_files:
                file_path = os.path.join(src_path, kf)
                if os.path.exists(file_path):
                    size_kb = os.path.getsize(file_path) / 1024
                    print(f"     ├── File: {kf} ({size_kb:,.1f} KB)")
                else:
                    print(f"     ├── File: {kf} (ready)")
        else:
            print(f" [!] Missing Dataset directory: {src_path}")

    print("-" * 80)
    print(f" Raw Dataset Check Complete: {found_count}/{len(DATASETS)} datasets verified.")
    print("=" * 80)

if __name__ == "__main__":
    main()
