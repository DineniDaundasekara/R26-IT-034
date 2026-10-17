# Employability research part: what it studies, how it works, and what is the research

This document describes the Employability part of the Career Intelligence Platform. It explains the research purpose, the three prediction phases, the live assessment pipeline, and which pieces are the research contribution.

The employability score is produced only by a frozen machine-learning model. The language model writes guidance from that evidence. It does not calculate or change the score.

## 1. What this research part studies

The research asks how a person's reported experience and behaviour relate to a continuous employability score on a 1 to 5 scale.

Three predictor domains are studied separately:

| Phase | Relationship | Survey | Predictor constructs | Frozen model |
| --- | --- | --- | --- | --- |
| 01 | Internship experience → employability | 12 Likert items (SIE1–SIE12) | Clear Objectives, School Support, Workplace Environment, Career Development | XGBoost |
| 02 | Competence → employability | 10 Likert items (C1–C10) | Life and Career Skills, Learning and Innovation Skills, IT and Media Skills | Linear regression, after standardisation |
| 03 | Psychological capital → employability | 12 Likert items (PsyCap1–PsyCap12) | Hope, Optimism, Resilience, Self-efficacy | ElasticNet, after standardisation |

Each item is answered from 1 to 5. A construct score is the mean of its items. The frozen model then predicts the employability value from those construct means.

The three phases are not combined into one statistical model. A person completes one phase at a time. Each phase has its own dataset, its own validation, and its own frozen model.

## 2. What is the research, and what is the software

The research contribution is the evidence chain below.

1. **Measurement.** Likert items are grouped into constructs that represent internship quality, competence, or psychological capital.
2. **Prediction.** A selected and validated regression model estimates a continuous employability score from those constructs. The model is then frozen. The live system does not retrain it.
3. **Explanation.** Tree SHAP is used for the XGBoost phase. Linear contributions are used for the linear regression and ElasticNet phases. These values explain how each construct influenced that prediction.
4. **Development priority.** The same frozen model is run again with one construct raised to 4.00 and the other answers unchanged. Priorities are ordered by the estimated change in the predicted score, not only by the lowest survey answer.
5. **Grounded guidance.** An OpenAI model turns that person's scores, explanation, and priority evidence into practical suggestions. If the API call fails, a rule-based text is used. In both cases the score stays the model score.
6. **Trusted learning sources.** Links are taken from a fixed library of university and official-provider pages. Only constructs below 4.00 receive links. The language model is not allowed to invent a web address.

The software is the way that chain is delivered: the assessment screens, the prediction service, the what-if control, and the PDF download. Those screens are the implementation. The research claim is the validated prediction and the evidence-grounded guidance, not the button layout.

## 3. How the research models were prepared

Each phase follows the same study sequence in its notebooks:

1. Data preprocessing
2. Reliability analysis
3. Descriptive statistics
4. Correlation analysis
5. Multiple linear regression
6. Feature engineering
7. Machine-learning experiments
8. Hyperparameter tuning
9. Explainable AI with SHAP
10. Recommendation design
11. Final validation and freezing of the selected model

After freezing, the live application loads the saved model file. It does not repeat the training.

### Figures recorded with the frozen models

Use the figure that belongs to the dataset and validation procedure you defend in the thesis. Two records currently exist, and they are not the same.

**Phase 01, XGBoost.** The earlier frozen result on the 1000-row development set was out-of-fold R² 0.469, MAE 0.172, RMSE 0.270. That is the figure still shown on the assessment screen. A later metadata file records an expanded set of 1224 rows, described there as real plus synthetic records with exact duplicates removed, with out-of-fold R² 0.882, MAE 0.230, and RMSE 0.317. The same note says Ridge was almost identical and XGBoost was kept so the existing Phase 01 model family and Tree SHAP pipeline stayed in place. That metadata also says expert validation of the recommendation mapping is still pending.

**Phase 02, linear regression.** The assessment screen shows test R² 0.546. The frozen-model metadata file records 1500 rows, an 80/20 split, test R² 0.930, MAE 0.179, RMSE 0.236, and repeated cross-validation mean R² 0.926. The pipeline is StandardScaler then Linear Regression. Status in that file is frozen.

**Phase 03, ElasticNet.** The assessment screen shows CV R² 0.574. The frozen-model metadata file records 1500 rows, nested cross-validation mean R² 0.933, test R² 0.918, MAE 0.178, and RMSE 0.271. The pipeline is StandardScaler then ElasticNet.

Before the thesis reports one of these numbers, confirm that the saved model file, the notebook, and the sentence in the chapter all refer to the same dataset.

## 4. What happens when a person uses the system

The live path is `POST /api/employability/{phase_id}/predict`.

1. The person answers every Likert item for the selected phase. Missing or non-numeric answers are rejected. Values outside 1 to 5 are rejected.
2. Each construct score is the arithmetic mean of its items.
3. The frozen model predicts one employability value from those construct scores. Phase 02 and Phase 03 apply the saved standardiser inside the model pipeline before the regression.
4. The service labels each construct as Strong (4.00 or above), Developing (3.00 to 3.99), or Needs Improvement (below 3.00). These words organise the screen. They are not a second classifier.
5. The three highest item scores are listed as strengths.
6. For every construct below 4.00, the service copies the answers, sets that one construct to 4.00, and predicts again. The difference is the estimated gain. Development priorities are the constructs with the largest positive gain, up to three. Each priority keeps a practical action. In Phase 01 the action is stored for the construct. In Phases 02 and 03 the action starts from the lowest item inside that construct, and the API may replace the wording with a suggestion grounded in the same evidence.
7. SHAP or linear contribution values are calculated for the constructs and placed in the evidence given to the guidance step.
8. The OpenAI API receives the predicted score, construct evidence, item scores, explanation values, and the impact ranking. It returns a career-readiness summary, strengths, improvement areas, an action plan, next steps, and area-level suggestions. The instruction to the API says it must not change the employability number, invent a URL, or claim that an improvement will necessarily raise employability.
9. If the API call fails, the same evidence is turned into rule-based sentences. The screen badge then says "Rule-based fallback guidance" instead of "OpenAI-grounded guidance".
10. Learning links are attached after the text is written. They come from the trusted library and are limited to constructs scoring below 4.00. This replacement is deliberate: the API writes the suggestions, and the system supplies the addresses.
11. The person can download the score, priorities, written guidance, and links as a PDF.

A second endpoint, `POST /api/employability/{phase_id}/what-if`, lets the person move one or more construct scores and see a new prediction from the same frozen model. The submitted answers are not overwritten. This step does not call the API and does not retrain the model.

## 5. How personalisation works

The result is personal because the inputs are personal.

- Different Likert answers produce different construct means.
- Different construct means produce a different model prediction.
- Different construct means change the SHAP or coefficient contribution of each construct.
- Different construct means change which area has the largest estimated gain when raised to 4.00.
- The API writes the summary and action plan from that evidence, so the sentences follow this person's scores.
- A construct at or above 4.00 does not receive a development link. A lower construct does.

What stays fixed is the model, the action library used as a starting point, the trusted web addresses, and the backup sentences used only when the API is unavailable. Two people with the same weak construct receive the same trusted course for that construct. Their written plans still differ when their other scores differ.

## 6. Trusted sources used for weaker areas

The library is limited to pages checked against the provider's own site. Examples used in the live library are:

- Open University OpenLearn courses on teamwork, management, thinking skills, and digital skills
- Google Career Certificates YouTube series on project management
- Imperial College London, "Creative Thinking: Techniques and Tools for Success", on Coursera
- Crash Course "Navigating Digital Information", produced with the Stanford History Education Group and the Poynter Institute
- UC Berkeley Greater Good resources, including Finding Silver Linings and The Science of Happiness
- UC Berkeley on edX, "Mindfulness and Resilience to Stress at Work"

Coursera and edX pages can be audited after the person creates an account. The link itself is the official course page.

## 7. What to claim, and what to keep out of the claim

Claims that match this implementation:

- Each phase predicts a continuous employability score from its own validated, frozen model.
- The explanation and the development order use that same model.
- The written guidance is conditioned on the person's evidence.
- The language model is separated from the score.
- Learning addresses are restricted to a checked library and are shown for the weaker constructs.

Claims this implementation does not support:

- The three phases do not form one combined employability model.
- Strength and development labels are not machine-learning classes.
- A higher construct score in the what-if tool is an estimate from the frozen model, not proof that a real intervention will raise employability.
- The API text is decision-support wording. It is not a clinical, hiring, or certification decision.
- Phase 01 metadata still records that expert validation of the recommendation mapping is pending.

## 8. Where the implementation lives

- Survey and results screen: `samindi/dashboard/frontend/src/views/EmployabilityView.jsx`
- Prediction, impact ranking, and what-if: `samindi/Employability/backend/employability_service.py`
- Phase 01, 02, and 03 guidance: `phase1_openai_guidance.py`, `phase2_openai_guidance.py`, `phase3_openai_guidance.py`
- Shared impact and trusted-link wording: `employability_impact.py`
- HTTP routes: `app/main.py`, under `/api/employability/{phase_id}/predict` and `/api/employability/{phase_id}/what-if`
- PDF: `samindi/dashboard/frontend/src/employabilityGuidancePdf.js`
- Frozen models: `samindi/Employability/backend/models`
- Study notebooks: `samindi/Employability/backend/notebooks`, with matching folders for Phase 02 competence and Phase 03 psychological capital
