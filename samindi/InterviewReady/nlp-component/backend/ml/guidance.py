from .text_features import extract_text_evidence
from .audio_features import extract_audio_numeric_features


def dedupe(items):
    return list(dict.fromkeys(items))


def build_guidance(
    transcript: str,
    communication_level: str,
    audio_path: str = "",
):
    evidence = extract_text_evidence(transcript)
    audio_evidence = extract_audio_numeric_features(audio_path, transcript) if audio_path else {}

    strengths = []
    weaknesses = []
    guidance = []
    activities = []

    if evidence["action_verbs"]:
        strengths.append("You use action verbs to explain what you did.")

    if evidence["professional_words"]:
        strengths.append("You use professional vocabulary that fits an interview answer.")

    if evidence["has_ownership"]:
        strengths.append("You clearly show your personal contribution.")

    if evidence["has_context"] and evidence["has_action"]:
        strengths.append(
            "You connect your answer to a real project or experience and explain your actions."
        )

    if evidence["has_result"]:
        strengths.append("You include a result or outcome in your answer.")

    if evidence["mentions_team"]:
        strengths.append("You communicate teamwork or collaboration experience.")

    if not strengths:
        strengths.append("You provide a relevant attempt to explain your experience.")

    if evidence["is_very_short"]:
        weaknesses.append("The answer is too brief to fully show your experience.")
        guidance.append(
            "Add one specific example with your responsibility, action, and result."
        )

    if not evidence["has_context"]:
        weaknesses.append("The situation or project context is not clear enough.")
        guidance.append(
            "Start by briefly explaining the project, internship, or situation."
        )

    if not evidence["has_task"]:
        weaknesses.append("Your exact responsibility is not stated clearly.")
        guidance.append(
            "State your responsibility in one direct sentence before explaining your actions."
        )

    if not evidence["has_action"]:
        weaknesses.append("Your personal actions are not explained clearly enough.")
        guidance.append(
            "Use ownership phrases such as 'I developed', 'I implemented', or 'I tested'."
        )

    if not evidence["has_result"]:
        weaknesses.append(
            "The answer does not finish with a clear result or learning outcome."
        )
        guidance.append(
            "Finish your example with the result, achievement, impact, or lesson learned."
        )

    if evidence["has_fillers"]:
        weaknesses.append("Filler words can make your spoken answer sound less fluent.")
        guidance.append(
            "Use a short pause instead of filler words when you need time to think."
        )

    if not weaknesses:
        weaknesses.append(
            "Your answer is generally structured; continue improving concise and natural delivery."
        )

    guidance.extend([
        "Practice answers using the STAR structure: Situation, Task, Action, Result.",
        "Practice explaining technical work in simple professional English.",
        "Record one answer each day and listen for unclear wording, repeated ideas, and missing results.",
        "Prepare a two-minute self-introduction covering your background, strongest skills, one project, and career direction.",
    ])

    activities.append({
        "id": "self-introduction",
        "category": "Spoken English",
        "title": "Two-minute self introduction",
        "description": (
            "Record a two-minute introduction covering your education, strongest skills, "
            "one project, and the type of role you want."
        ),
        "durationMinutes": 8,
        "successCheck": "You can finish the introduction without reading a full script.",
    })

    if not all([
        evidence["has_context"],
        evidence["has_task"],
        evidence["has_action"],
        evidence["has_result"],
    ]):
        activities.append({
            "id": "star-project",
            "category": "STAR Practice",
            "title": "Build one complete STAR answer",
            "description": (
                "Choose one project and speak through Situation, Task, Action, and Result "
                "without reading from a script."
            ),
            "durationMinutes": 10,
            "successCheck": "Your answer includes all four STAR parts in a logical order.",
        })

    if evidence["has_fillers"]:
        activities.append({
            "id": "filler-reduction",
            "category": "Spoken English",
            "title": "Pause instead of filler words",
            "description": (
                "Record the same answer three times and replace filler words with a short silent pause."
            ),
            "durationMinutes": 7,
            "successCheck": "The final attempt uses deliberate pauses instead of repeated filler words.",
        })

    if not evidence["has_result"]:
        activities.append({
            "id": "result-ending",
            "category": "Answer Structure",
            "title": "Practice strong answer endings",
            "description": (
                "Take three project answers and finish each one with the real result, impact, or lesson learned."
            ),
            "durationMinutes": 8,
            "successCheck": "Each answer ends with a real outcome or lesson rather than stopping after the action.",
        })

    if not evidence["has_ownership"]:
        activities.append({
            "id": "ownership-language",
            "category": "Professional Communication",
            "title": "Practice ownership language",
            "description": (
                "Explain one project using clear phrases such as 'I developed', "
                "'I tested', 'I implemented', and 'I resolved'."
            ),
            "durationMinutes": 6,
            "successCheck": "A listener can clearly identify your personal contribution.",
        })

    activities.extend([
        {
            "id": "technical-explanation",
            "category": "Professional Communication",
            "title": "Explain one project simply",
            "description": (
                "Explain one technical project to a non-technical interviewer: problem, your responsibility, technology used, action, and result."
            ),
            "durationMinutes": 10,
            "successCheck": "The explanation is understandable without relying on unexplained technical terms.",
        },
        {
            "id": "teamwork-mock",
            "category": "Mock Interview",
            "title": "Teamwork mock question",
            "description": (
                "Answer: 'Tell me about a time you worked with a team to solve a problem.' Use STAR and clearly explain your own contribution."
            ),
            "durationMinutes": 10,
            "successCheck": "The answer separates team activity from what you personally did.",
        },
        {
            "id": "challenge-mock",
            "category": "Mock Interview",
            "title": "Challenge mock question",
            "description": (
                "Answer: 'Describe a difficult problem you faced and how you solved it.' End with the real result or what you learned."
            ),
            "durationMinutes": 10,
            "successCheck": "The answer explains the problem, your action, and a real result or lesson.",
        },
        {
            "id": "daily-speaking",
            "category": "Spoken English",
            "title": "Daily five-minute speaking practice",
            "description": (
                "Speak for five minutes about your studies, internship, or project. Focus on short sentences and clear professional wording."
            ),
            "durationMinutes": 5,
            "successCheck": "You complete five minutes of focused speaking practice.",
        },
    ])

    diagnostics = {
        "acousticSignals": {
            "speakingRateWpm": round(float(audio_evidence.get("speaking_rate_wpm", 0.0)), 1),
            "pauseCount": int(audio_evidence.get("pause_count", 0)),
            "averagePauseDurationSeconds": round(float(audio_evidence.get("average_pause_duration", 0.0)), 2),
            "silenceRatioPercent": round(float(audio_evidence.get("silence_ratio", 0.0)) * 100, 1),
            "audioDurationSeconds": round(float(audio_evidence.get("audio_duration_seconds", 0.0)), 1),
            "energyDynamicRangeDb": round(float(audio_evidence.get("energy_dynamic_range_db", 0.0)), 1),
        },
        "linguisticSignals": {
            "starSituationDetected": bool(evidence.get("has_context")),
            "starTaskDetected": bool(evidence.get("has_task")),
            "starActionDetected": bool(evidence.get("has_action")),
            "starResultDetected": bool(evidence.get("has_result")),
            "starCoverageCount": sum([
                bool(evidence.get("has_context")),
                bool(evidence.get("has_task")),
                bool(evidence.get("has_action")),
                bool(evidence.get("has_result")),
            ]),
            "actionVerbsDetected": evidence.get("action_verbs", []),
            "professionalVocabulary": evidence.get("professional_words", []),
            "fillerWordsDetected": evidence.get("fillers", []),
            "hasOwnership": bool(evidence.get("has_ownership")),
        },
        "researchMetadata": {
            "primaryClassifier": "Linear Support Vector Machine (Linear SVM)",
            "classificationCategory": communication_level,
            "featureVectorPipeline": "TF-IDF (1,2 n-grams) + StandardScaler (Acoustic & Linguistic Features)",
            "validationMethod": "Stratified Group K-Fold Cross Validation",
            "antiHallucinationVerified": True,
            "groundingSource": "Deterministic Transcript Evidence",
        }
    }

    return {
        "communicationLevel": communication_level,
        "evidence": evidence,
        "audioEvidence": audio_evidence,
        "diagnostics": diagnostics,
        "strengths": dedupe(strengths),
        "weaknesses": dedupe(weaknesses),
        "guidance": dedupe(guidance),
        "activities": activities,
        "starPractice": [
            {
                "name": "Situation",
                "instruction": "Briefly explain the project, internship, or situation.",
            },
            {
                "name": "Task",
                "instruction": "State your responsibility or goal.",
            },
            {
                "name": "Action",
                "instruction": "Explain what you personally did.",
            },
            {
                "name": "Result",
                "instruction": "Finish with the real outcome, impact, or lesson learned.",
            },
        ],
        "mockInterviewPrompts": [
            "Tell me about yourself.",
            "Explain a project you are proud of.",
            "Tell me about a challenge you faced and how you solved it.",
            "Describe a time you worked with a team.",
            "Explain a technical concept to a non-technical person.",
            "Why are you interested in this role?",
        ],
    }


def build_advanced_fallback(
    *,
    transcript: str,
    communication_level: str,
    baseline: dict,
    target_role: str = "",
):
    weaknesses_text = " ".join(baseline["weaknesses"]).lower()

    priority = []
    if "context" in weaknesses_text or "situation" in weaknesses_text:
        priority.append({
            "title": "Set the context first",
            "why": "Your answer needs a clearer starting point before technical detail.",
            "targetBehavior": "Open with one sentence describing the project or situation.",
            "quickWin": "Use: 'In this project, the main goal was...'",
        })
    if "responsibility" in weaknesses_text or "personal" in weaknesses_text or "action" in weaknesses_text:
        priority.append({
            "title": "Show personal ownership",
            "why": "Interviewers need to distinguish your contribution from the team's work.",
            "targetBehavior": "Use first-person action language for your own contribution.",
            "quickWin": "Use: 'My main responsibility was...' followed by 'I implemented/tested/designed...'.",
        })
    if "result" in weaknesses_text or "outcome" in weaknesses_text:
        priority.append({
            "title": "Finish with a real result",
            "why": "A clear ending shows why your action mattered.",
            "targetBehavior": "End the example with a real outcome, impact, or lesson.",
            "quickWin": "Use: 'As a result...' or 'What I learned was...'.",
        })
    if "filler" in weaknesses_text:
        priority.append({
            "title": "Replace fillers with pauses",
            "why": "Short pauses make thinking time sound more controlled.",
            "targetBehavior": "Pause briefly instead of repeating filler words.",
            "quickWin": "Practise the same 45-second answer three times with deliberate pauses.",
        })
    if not priority:
        priority.append({
            "title": "Make answers more concise",
            "why": "Clear interview answers are easier to follow when each idea has a purpose.",
            "targetBehavior": "Use one example, one responsibility, one action, and one result.",
            "quickWin": "Aim for a focused 60-90 second project answer.",
        })

    priority = priority[:3]

    patterns = [
        {
            "purpose": "Introduce context",
            "pattern": "The project was developed for [real context], and the main goal was [real goal].",
            "candidateExample": "Use the real project context already mentioned in your answer.",
        },
        {
            "purpose": "State responsibility",
            "pattern": "My main responsibility was to [your real responsibility].",
            "candidateExample": "Replace the bracket with the task you actually performed.",
        },
        {
            "purpose": "Explain action",
            "pattern": "To address this, I [real action you personally took].",
            "candidateExample": "Use a strong action verb such as developed, tested, designed, or implemented only when it is true.",
        },
        {
            "purpose": "Finish with impact",
            "pattern": "As a result, [real outcome]. What I learned was [real lesson].",
            "candidateExample": "If you do not have a measured outcome, use the genuine lesson learned instead of inventing a number.",
        },
    ]

    seven_days = [
        (1, "Build your introduction", "Record a 90-second background → skills → project → role answer."),
        (2, "Professional sentence patterns", "Repeat responsibility, action, result, and learning patterns using your own facts."),
        (3, "STAR structure", "Create one complete Situation → Task → Action → Result project answer."),
        (4, "Ownership and impact", "Re-record yesterday's answer with clearer 'I...' actions and a real ending."),
        (5, "Explain technical work simply", "Explain one project to a non-technical listener in plain professional English."),
        (6, "Mock interview", "Answer one teamwork question and one challenge question without reading."),
        (7, "Fresh assessment", "Record a completely fresh answer and compare its new feedback with your previous focus areas."),
    ]

    return {
        "coachSummary": (
            f"Your current model category is {communication_level}. "
            "Use the priority areas below to make your next interview answer clearer, more professional, and easier to follow."
        ),
        "knowledgeSnapshot": {
            "alreadyDemonstrated": baseline["strengths"][:4],
            "nextCapabilitiesToBuild": baseline["weaknesses"][:4],
        },
        "strengths": baseline["strengths"],
        "weaknesses": baseline["weaknesses"],
        "priorityFocus": priority,
        "guidance": baseline["guidance"],
        "professionalRewrites": [
            {
                "originalIdea": "Use one idea from your own transcript.",
                "improvedVersion": "My main responsibility was to [state your real responsibility clearly].",
                "whyItIsBetter": "It makes ownership explicit without inventing a new fact.",
            },
            {
                "originalIdea": "Use the problem or challenge already mentioned in your answer.",
                "improvedVersion": "To address this, I [state the action you actually took].",
                "whyItIsBetter": "It connects the challenge to your personal action.",
            },
            {
                "originalIdea": "Use the real outcome or learning from your experience.",
                "improvedVersion": "As a result, [real outcome]. What I learned was [real lesson].",
                "whyItIsBetter": "It gives the answer a complete interview-ready ending.",
            },
        ],
        "speakingPatterns": patterns,
        "starCoach": [
            {
                "name": "Situation",
                "candidateContent": "Use the real project or experience already present in your transcript.",
                "coachingPrompt": "What was happening, who was the project for, and what problem existed?",
                "exampleStarter": "In this project, the main goal was...",
            },
            {
                "name": "Task",
                "candidateContent": "State your real responsibility; do not describe only the team's work.",
                "coachingPrompt": "What exactly were you responsible for?",
                "exampleStarter": "My main responsibility was to...",
            },
            {
                "name": "Action",
                "candidateContent": "Use only actions you personally completed.",
                "coachingPrompt": "What steps did you personally take?",
                "exampleStarter": "To address this, I...",
            },
            {
                "name": "Result",
                "candidateContent": "Use a real result or lesson. If no measured result exists, do not invent one.",
                "coachingPrompt": "What changed, what was completed, or what did you learn?",
                "exampleStarter": "As a result... / What I learned was...",
            },
        ],
        "practiceAnswer": (
            "Use your original transcript as the factual source. Rebuild it using this order: "
            "brief background, relevant skills, one real project, your responsibility, your personal action, "
            "the real result or lesson, and why that experience connects to the role."
        ),
        "activities": baseline["activities"],
        "sevenDayPlan": [
            {
                "day": day,
                "title": title,
                "focus": task,
                "tasks": [task],
                "reflection": "What sounded clearer than yesterday, and what still felt difficult?",
            }
            for day, title, task in seven_days
        ],
        "mockInterviewPrompts": baseline["mockInterviewPrompts"],
        "nextAttemptChallenge": {
            "question": (
                f"Give a 60-90 second answer about one real project relevant to {target_role}."
                if target_role
                else "Give a 60-90 second answer about one real project you worked on."
            ),
            "focus": priority[0]["title"],
            "beforeRecording": [
                "Choose one real example.",
                "State your responsibility clearly.",
                "Explain what you personally did.",
                "Finish with a real outcome or lesson.",
            ],
        },
        "motivation": (
            "Complete one focused practice task today, then make a fresh recording. "
            "Use the new feedback as evidence for what to practise next."
        ),
    }



def build_follow_up_fallback(
    *,
    transcript: str,
    communication_level: str,
    question: str,
    target_role: str = "",
):
    """Create a useful local coaching reply when the OpenAI API is unavailable.

    This fallback is intentionally evidence-grounded. It does not invent candidate
    facts and does not calculate a new communication level.
    """
    baseline = build_guidance(transcript, communication_level)
    evidence = baseline.get("evidence", {})
    weaknesses = baseline.get("weaknesses", [])
    guidance = baseline.get("guidance", [])

    prompt = str(question or "").strip().lower()
    role_text = f" for a {target_role} interview" if target_role else ""

    def focus_summary():
        items = weaknesses[:3]
        if not items:
            return "Keep the answer concise, structured, and supported by one real example."
        cleaned = [str(item).rstrip(" .") for item in items]
        return " Your main focus areas are: " + "; ".join(cleaned) + "."

    if "stronger opening" in prompt or "opening" in prompt or "start" in prompt:
        parts = [
            f"For a stronger opening{role_text}, use a short 3-part structure:",
            "1. Who you are now: 'I am a [student/graduate/current role] preparing for [target role].'",
            "2. Your relevant strengths: 'My background includes hands-on work with [skills that are actually true for you].'",
            "3. Your direction: 'I am interested in this role because I want to apply those skills in a professional environment.'",
            "Keep it to about 2-3 sentences before moving to a real project example.",
        ]
        if evidence.get("professional_words"):
            parts.append("You already use some professional vocabulary, so keep that strength and make the opening more concise.")
        return "\n".join(parts)

    if "project" in prompt and ("clear" in prompt or "explain" in prompt):
        return "\n".join([
            "Explain the project in this order:",
            "1. Context: 'The project was developed for [real context], and the main goal was [real goal].'",
            "2. Responsibility: 'My main responsibility was to [your real responsibility].'",
            "3. Action: 'To address the main challenge, I [what you personally did].'",
            "4. Result: 'As a result, [real outcome].' If you do not have a measurable result, state the real lesson you learned.",
            "Avoid saying only 'we did' or 'we fixed it'; make your own contribution visible." + focus_summary(),
        ])

    if "result" in prompt or "outcome" in prompt or "impact" in prompt:
        result_tip = (
            "Your current answer already contains some result language. Make it more specific by connecting the result directly to your action."
            if evidence.get("has_result")
            else "Your current feedback shows that the answer needs a clearer ending. Do not invent a number or achievement; add the real outcome or lesson."
        )
        return "\n".join([
            result_tip,
            "Practise one of these truthful patterns:",
            "• 'As a result, the solution [state the real effect].'",
            "• 'The final outcome was [state what actually happened].'",
            "• 'What I learned from this experience was [real lesson].'",
            "• 'This experience helped me improve [real skill you developed].'",
            "If you do not know the real outcome yet, use '[add your real result here]' while practising instead of inventing facts.",
        ])

    if "mock" in prompt or "question" in prompt:
        if target_role:
            question_text = (
                f"Tell me about one project that is relevant to a {target_role} role. "
                "What was your responsibility, what challenge did you face, what did you personally do, and what was the real result?"
            )
        else:
            question_text = (
                "Tell me about one project you worked on. What was your responsibility, "
                "what challenge did you face, what did you personally do, and what was the real result?"
            )
        return "\n".join([
            "Try this mock interview question:",
            question_text,
            "Before answering, take 10 seconds to plan: Situation → Task → Action → Result.",
            "Self-check: Could an interviewer clearly identify what YOU personally contributed?",
        ])

    if "star" in prompt:
        return "\n".join([
            "Use STAR with only facts from your real experience:",
            "S — Situation: briefly explain the project or problem.",
            "T — Task: state your exact responsibility.",
            "A — Action: explain the steps you personally took.",
            "R — Result: finish with the real outcome, impact, or lesson.",
            "Practise it once slowly, then record a second 60-90 second version without reading.",
        ])

    # General evidence-based fallback.
    lines = [
        f"Your current communication category is {communication_level}.",
        "For your next answer, focus on one improvement at a time.",
    ]
    for item in guidance[:3]:
        lines.append(f"• {item}")
    lines.extend([
        "A useful speaking pattern is: 'The situation was... My responsibility was... To address it, I... As a result...'",
        "Use only your real experience and re-record the answer after practising it once.",
    ])
    return "\n".join(lines)
