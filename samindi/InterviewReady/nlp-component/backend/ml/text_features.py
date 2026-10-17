import re


FILLER_PHRASES = [
    "um",
    "uh",
    "erm",
    "hmm",
    "you know",
    "basically",
]

ACTION_VERBS = {
    "built",
    "created",
    "developed",
    "designed",
    "implemented",
    "integrated",
    "tested",
    "deployed",
    "managed",
    "led",
    "improved",
    "optimized",
    "resolved",
    "automated",
    "configured",
    "analysed",
    "analyzed",
    "delivered",
    "maintained",
    "supported",
    "coordinated",
    "prepared",
    "planned",
}

PROFESSIONAL_WORDS = {
    "responsible",
    "collaborated",
    "experience",
    "project",
    "requirement",
    "requirements",
    "solution",
    "quality",
    "customer",
    "client",
    "team",
    "deadline",
    "testing",
    "deployment",
    "integration",
    "performance",
    "security",
    "challenge",
    "objective",
    "analysis",
    "development",
}

RESULT_WORDS = {
    "result",
    "results",
    "achieved",
    "completed",
    "delivered",
    "improved",
    "reduced",
    "increased",
    "saved",
    "successfully",
    "outcome",
    "resolved",
    "enhanced",
    "finished",
}

CONTEXT_WORDS = {
    "during",
    "when",
    "while",
    "project",
    "internship",
    "experience",
    "situation",
    "previously",
    "university",
}

TASK_WORDS = {
    "responsible",
    "task",
    "goal",
    "objective",
    "assigned",
    "required",
    "requirement",
    "needed",
    "role",
}

OWNERSHIP_PHRASES = [
    "i developed",
    "i built",
    "i created",
    "i designed",
    "i implemented",
    "i integrated",
    "i tested",
    "i managed",
    "i resolved",
    "i improved",
    "i was responsible",
    "my responsibility",
    "i contributed",
    "my role",
]


def normalize_text(text: str) -> str:
    value = str(text or "").lower().strip()
    return re.sub(r"\s+", " ", value)


def tokenize(text: str):
    return re.findall(
        r"\b[a-zA-Z']+\b",
        normalize_text(text)
    )


def phrase_count(text: str, phrases) -> int:
    normalized = normalize_text(text)
    total = 0

    for phrase in phrases:
        total += len(
            re.findall(
                rf"\b{re.escape(phrase)}\b",
                normalized,
                flags=re.IGNORECASE,
            )
        )

    return total


def extract_text_numeric_features(text: str) -> dict:
    normalized = normalize_text(text)
    words = tokenize(normalized)
    word_set = set(words)

    word_count = len(words)

    sentences = [
        item.strip()
        for item in re.split(r"[.!?]+", str(text or ""))
        if item.strip()
    ]

    sentence_count = len(sentences)

    filler_count = phrase_count(
        normalized,
        FILLER_PHRASES
    )

    action_verb_count = sum(
        1 for word in words
        if word in ACTION_VERBS
    )

    professional_word_count = sum(
        1 for word in words
        if word in PROFESSIONAL_WORDS
    )

    result_word_count = sum(
        1 for word in words
        if word in RESULT_WORDS
    )

    ownership_phrase_count = phrase_count(
        normalized,
        OWNERSHIP_PHRASES
    )

    return {
        "word_count": float(word_count),
        "sentence_count": float(sentence_count),
        "average_sentence_length": (
            float(word_count / sentence_count)
            if sentence_count
            else float(word_count)
        ),
        "vocabulary_diversity": (
            float(len(word_set) / word_count)
            if word_count
            else 0.0
        ),
        "filler_count": float(filler_count),
        "filler_ratio": (
            float(filler_count / word_count)
            if word_count
            else 0.0
        ),
        "action_verb_count": float(action_verb_count),
        "professional_word_count": float(professional_word_count),
        "result_word_count": float(result_word_count),
        "ownership_phrase_count": float(ownership_phrase_count),
        "star_context": float(
            any(word in word_set for word in CONTEXT_WORDS)
        ),
        "star_task": float(
            any(word in word_set for word in TASK_WORDS)
        ),
        "star_action": float(action_verb_count > 0),
        "star_result": float(result_word_count > 0),
    }


def extract_text_evidence(text: str) -> dict:
    normalized = normalize_text(text)
    words = tokenize(normalized)
    word_set = set(words)
    numeric = extract_text_numeric_features(text)

    return {
        "has_context": bool(numeric["star_context"]),
        "has_task": bool(numeric["star_task"]),
        "has_action": bool(numeric["star_action"]),
        "has_result": bool(numeric["star_result"]),
        "has_ownership": bool(numeric["ownership_phrase_count"]),
        "has_fillers": bool(numeric["filler_count"]),
        "is_very_short": numeric["word_count"] < 35,
        "action_verbs": sorted(
            {word for word in words if word in ACTION_VERBS}
        ),
        "professional_words": sorted(
            {word for word in words if word in PROFESSIONAL_WORDS}
        ),
        "result_words": sorted(
            {word for word in words if word in RESULT_WORDS}
        ),
        "mentions_team": "team" in word_set
        or "collaborated" in word_set
        or "teamwork" in word_set,
    }
