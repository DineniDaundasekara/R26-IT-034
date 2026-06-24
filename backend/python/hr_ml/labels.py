"""
SkillVerify Epistemic Class Labels & Classification Standards
=============================================================
Defines the 4-way Epistemic Natural Language Inference (NLI) categories,
human-readable status strings, UI pill badges, and numerical mappings.
"""

from typing import Dict, Any, List

# 4-Way Epistemic Verification Classes
CLASSES: List[str] = [
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "INSUFFICIENT_EVIDENCE",
    "POTENTIAL_CONTRADICTION"
]

CLASS_TO_IDX: Dict[str, int] = {c: i for i, c in enumerate(CLASSES)}
IDX_TO_CLASS: Dict[int, str] = {i: c for i, c in enumerate(CLASSES)}

# Detailed Metadata per Epistemic State
LABEL_METADATA: Dict[str, Dict[str, Any]] = {
    "SUPPORTED": {
        "title": "Verified with Public Code",
        "description": "Corroborated by independent public repositories, commits, and matching timeline span (Tenure Ratio R >= 0.70).",
        "badgeColor": "green",
        "statusPill": "status-pill-verified",
        "isPenalty": False,
        "isVerified": True
    },
    "PARTIALLY_SUPPORTED": {
        "title": "Partially Verified (Shorter Public Span)",
        "description": "Public repository code exists, but observed commit timeline span is shorter than claimed on the resume (0 < R < 0.70).",
        "badgeColor": "amber",
        "statusPill": "status-pill-partial",
        "isPenalty": False,
        "isVerified": True
    },
    "INSUFFICIENT_EVIDENCE": {
        "title": "Private Experience (Unobserved on Public GitHub)",
        "description": "Claimed on resume but not detected on public GitHub. Standard for corporate/enterprise developers; no penalty assigned.",
        "badgeColor": "slate",
        "statusPill": "status-pill-unobserved",
        "isPenalty": False,
        "isVerified": False
    },
    "POTENTIAL_CONTRADICTION": {
        "title": "Timeline Discrepancy (Chronological Impossibility)",
        "description": "Claimed experience exceeds the existence duration of the technology (e.g. claiming 15 years of React in 2026).",
        "badgeColor": "red",
        "statusPill": "status-pill-contradiction",
        "isPenalty": True,
        "isVerified": False
    }
}

# Master Verdict Recommendation Types
VERDICT_TYPES = {
    "SUITABLE": {
        "text": "This employee is suitable for our job.",
        "badge": "SUITABLE",
        "theme": "green",
        "minScore": 80
    },
    "PARTIALLY_SUITABLE": {
        "text": "This employee is partially suitable for our job (Skill upskilling recommended).",
        "badge": "PARTIALLY_SUITABLE",
        "theme": "amber",
        "minScore": 60
    },
    "NOT_SUITABLE": {
        "text": "This employee is not suitable for our job.",
        "badge": "NOT_SUITABLE",
        "theme": "red",
        "minScore": 0
    }
}


def get_label_info(status: str) -> Dict[str, Any]:
    """Returns label metadata dictionary for a given verification status."""
    return LABEL_METADATA.get(status, {
        "title": status,
        "description": "Unclassified verification status.",
        "badgeColor": "slate",
        "statusPill": "status-pill-unobserved",
        "isPenalty": False,
        "isVerified": False
    })
