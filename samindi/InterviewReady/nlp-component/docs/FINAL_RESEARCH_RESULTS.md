# Latest Duplicate-Safe Research Results

These values come from the latest training output supplied during the project workflow.

## Dataset

- Total interviews: 248
- Average: 141
- Good: 46
- Poor: 40
- Excellent: 21
- Rows belonging to exact duplicate transcript groups: 80
- Exact duplicate groups: 30
- Unique transcript groups: 198
- Research training rows: 198
- Held-out test rows: 50

## Validation design

- Exact normalized transcript copies were assigned to the same SHA-1 transcript group.
- Held-out split: `StratifiedGroupKFold`
- Cross-validation: 5-fold `StratifiedGroupKFold` on the research training partition.
- Primary model-selection metric: Macro-F1.
- Held-out test results were not used to choose the model.

## Model comparison

| Model | Group CV Macro-F1 | CV Std | Held-out Macro-F1 | Held-out Accuracy |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.8190 | 0.0676 | 0.7898 | 0.80 |
| **Linear SVM** | **0.8450** | 0.0531 | **0.8249** | **0.86** |
| Random Forest | 0.7727 | **0.0384** | 0.7654 | 0.82 |

## Selected final model

**Linear SVM**, because it obtained the highest mean group-aware cross-validated Macro-F1 on the training partition.

## Correct viva sentence

> I compared Logistic Regression, Linear SVM, and Random Forest using five-fold Stratified Group Cross-Validation. I used Macro-F1 as the primary selection metric because the communication classes were imbalanced. Exact duplicate transcripts were grouped so identical answers could not appear on both sides of validation. Linear SVM achieved the highest mean cross-validated Macro-F1, approximately 0.845, and was therefore selected. The held-out test Macro-F1 was approximately 0.825 with 86% accuracy. These metrics are for research validation and are not displayed to candidates.
