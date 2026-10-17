import json
import re
from typing import List

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from .config import (
    OPENAI_API_KEY,
    OPENAI_GUIDANCE_ENABLED,
    OPENAI_GUIDANCE_MODEL,
    OPENAI_GUIDANCE_VERIFY,
    OPENAI_VERIFIER_MODEL,
)


class FocusItem(BaseModel):
    title: str
    why: str
    targetBehavior: str
    quickWin: str


class RewriteItem(BaseModel):
    originalIdea: str
    improvedVersion: str
    whyItIsBetter: str


class SpeakingPattern(BaseModel):
    purpose: str
    pattern: str
    candidateExample: str


class StarStep(BaseModel):
    name: str
    candidateContent: str
    coachingPrompt: str
    exampleStarter: str


class Activity(BaseModel):
    id: str
    category: str
    title: str
    description: str
    durationMinutes: int = Field(ge=3, le=30)
    successCheck: str


class DayPlan(BaseModel):
    day: int = Field(ge=1, le=7)
    title: str
    focus: str
    tasks: List[str]
    reflection: str


class NextChallenge(BaseModel):
    question: str
    focus: str
    beforeRecording: List[str]


class KnowledgeSnapshot(BaseModel):
    alreadyDemonstrated: List[str]
    nextCapabilitiesToBuild: List[str]


class CoachResponse(BaseModel):
    coachSummary: str
    knowledgeSnapshot: KnowledgeSnapshot
    strengths: List[str]
    weaknesses: List[str]
    priorityFocus: List[FocusItem]
    guidance: List[str]
    professionalRewrites: List[RewriteItem]
    speakingPatterns: List[SpeakingPattern]
    starCoach: List[StarStep]
    practiceAnswer: str
    activities: List[Activity]
    sevenDayPlan: List[DayPlan]
    mockInterviewPrompts: List[str]
    nextAttemptChallenge: NextChallenge
    motivation: str


SYSTEM_INSTRUCTIONS = """
You are an evidence-grounded interview communication coach for university students and early-career candidates.

You receive a transcript, an ML-predicted communication level, deterministic evidence extracted from that transcript, and optional role context.

NON-NEGOTIABLE RULES:
1. The ML communication level is authoritative. Never change, override, soften, or recompute it.
2. Never invent candidate facts: no fake projects, employers, technologies, achievements, dates, responsibilities, metrics, or outcomes.
3. When creating a better practice answer, improve only structure and professional wording using facts already present in the transcript. If a fact is missing, use a neutral placeholder such as "[add your real result here]" rather than inventing one.
4. Treat the transcript as speech-to-text output that may contain recognition errors. Do not infer new facts from unclear words.
5. Base strengths and weaknesses on observable evidence. Do not diagnose personality, intelligence, confidence, mental health, or language ability.
6. Do not output scores, percentages, probabilities, confidence values, or fabricated measurements.
7. Guidance must be practical: what to say, how to practise it, and how the candidate can self-check it.
8. Keep English clear and professional, suitable for a university final-year research system.
9. The 7-day plan is a practice plan, not a claim that skill will improve by a fixed amount.
10. Return JSON only. Do not use Markdown fences.
""".strip()


def _extract_json(text: str) -> dict:
    value = str(text or "").strip()
    value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*```$", "", value)

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        start = value.find("{")
        end = value.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(value[start:end + 1])


def _compact_evidence(evidence: dict) -> dict:
    allowed = {
        "has_context",
        "has_task",
        "has_action",
        "has_result",
        "has_ownership",
        "has_fillers",
        "is_very_short",
        "action_verbs",
        "professional_words",
        "result_words",
        "mentions_team",
    }
    return {
        key: evidence.get(key)
        for key in allowed
        if key in evidence
    }


def generate_ai_guidance(
    *,
    transcript: str,
    communication_level: str,
    evidence: dict,
    deterministic_guidance: dict,
    target_role: str = "",
    experience_level: str = "",
    practice_goal: str = "",
):
    if not OPENAI_GUIDANCE_ENABLED or not OPENAI_API_KEY:
        return None

    schema = CoachResponse.model_json_schema()

    payload = {
        "communicationLevel": communication_level,
        "targetRole": target_role or "Not provided",
        "experienceLevel": experience_level or "Not provided",
        "practiceGoal": practice_goal or "Improve interview communication",
        "transcript": transcript,
        "observableEvidence": _compact_evidence(evidence),
        "deterministicBaseline": {
            "strengths": deterministic_guidance.get("strengths", []),
            "weaknesses": deterministic_guidance.get("weaknesses", []),
            "guidance": deterministic_guidance.get("guidance", []),
        },
    }

    prompt = f"""
Create a personalized interview communication improvement plan from the supplied evidence.

The response MUST match this JSON Schema exactly:
{json.dumps(schema, ensure_ascii=False)}

Quality requirements:
- 2-5 evidence-grounded strengths.
- 2-5 priority weaknesses, phrased constructively and specifically.
- Exactly 3 priorityFocus items whenever enough evidence exists; otherwise use the available priorities.
- 3-5 professionalRewrites. Each rewrite must correspond to an idea actually found in the transcript.
- 4-6 speakingPatterns with reusable sentence structures and examples grounded in the candidate's own content.
- starCoach should contain Situation, Task, Action, Result. If a part is missing, candidateContent must say it is missing and coachingPrompt must tell the candidate what real information to add.
- practiceAnswer should sound interview-ready but must not invent facts. Aim for about 120-180 words when the transcript has enough content.
- 6-9 activities. Make them measurable by completion, not by a fake skill score.
- sevenDayPlan must contain exactly Day 1 through Day 7, with small realistic daily tasks.
- 5-7 mock interview prompts tailored to the target role when supplied, otherwise tailored to the candidate's transcript.
- nextAttemptChallenge should prepare the candidate for one fresh recording.
- motivation should be encouraging but factual; never claim an improvement that has not been measured.

INPUT:
{json.dumps(payload, ensure_ascii=False)}
""".strip()

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.responses.create(
        model=OPENAI_GUIDANCE_MODEL,
        instructions=SYSTEM_INSTRUCTIONS,
        input=prompt,
    )

    raw = response.output_text
    parsed = _extract_json(raw)

    try:
        validated = CoachResponse.model_validate(parsed)
    except ValidationError as error:
        raise RuntimeError(
            "OpenAI guidance returned JSON that did not match the expected schema."
        ) from error

    generated = validated.model_dump()

    if not OPENAI_GUIDANCE_VERIFY:
        return generated

    verifier_prompt = f"""
You are the grounding verifier for an interview communication coaching system.

ORIGINAL TRANSCRIPT:
{transcript}

AUTHORITATIVE ML LEVEL:
{communication_level}

TARGET ROLE:
{target_role or 'Not provided'}

GENERATED COACHING JSON:
{json.dumps(generated, ensure_ascii=False)}

EXPECTED JSON SCHEMA:
{json.dumps(schema, ensure_ascii=False)}

Verify and correct the coaching JSON.
- Remove or rewrite any claim that is not supported by the transcript.
- Do not add candidate facts.
- Do not change the ML communication level; the level is not part of this JSON.
- Professional rewrites may improve wording but must preserve the original facts.
- A practice answer must use only transcript facts; if an outcome is missing, use a neutral placeholder such as [add your real result here].
- Keep guidance practical, clear, and suitable for interview practice.
- Return one JSON object matching the schema exactly. No Markdown.
""".strip()

    verifier_response = client.responses.create(
        model=OPENAI_VERIFIER_MODEL,
        instructions=(
            "You are a strict factual grounding verifier. Return corrected JSON only. "
            "Never invent candidate experience, metrics, employers, technologies, achievements, or results."
        ),
        input=verifier_prompt,
    )

    verified_raw = verifier_response.output_text
    verified_parsed = _extract_json(verified_raw)
    try:
        verified = CoachResponse.model_validate(verified_parsed)
    except ValidationError as error:
        raise RuntimeError(
            "OpenAI grounding verifier returned JSON that did not match the expected schema."
        ) from error

    return verified.model_dump()


def generate_follow_up(
    *,
    transcript: str,
    communication_level: str,
    question: str,
    target_role: str = "",
):
    if not OPENAI_GUIDANCE_ENABLED or not OPENAI_API_KEY:
        return None

    prompt = f"""
Candidate transcript:
{transcript}

Authoritative ML communication level:
{communication_level}

Target role:
{target_role or 'Not provided'}

Candidate question to the coach:
{question}

Answer the candidate's question as an interview communication coach.
Use only facts present in the transcript. You may improve wording and structure, but do not invent experience, achievements, technologies, or metrics.
Do not provide percentages, confidence scores, or a new communication level.
Keep the answer practical and concise. When useful, give a short example phrase the candidate can practise aloud.
""".strip()

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.responses.create(
        model=OPENAI_GUIDANCE_MODEL,
        instructions=SYSTEM_INSTRUCTIONS.replace(
            "10. Return JSON only. Do not use Markdown fences.",
            "10. For this follow-up request, return concise plain text, not JSON.",
        ),
        input=prompt,
    )
    return response.output_text.strip()
