"""Wording helpers for construct-level employability impact.

The score change itself is computed by the frozen model in
employability_service. These helpers only turn that ranking into guidance
text so the three phase recommendation modules stay consistent.
"""

from typing import Any, Dict, List


def positive_impact_rows(ranking: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [row for row in (ranking or []) if float(row.get("expected_gain") or 0) > 0]


def priority_labels(ranking: List[Dict[str, Any]], limit: int = 3) -> List[str]:
    labels = []
    for row in positive_impact_rows(ranking)[:limit]:
        labels.append(
            f"{row['name']} (raise from {float(row['current_score']):.2f} to "
            f"{float(row['target_score']):.2f}, estimated gain +{float(row['expected_gain']):.2f})"
        )
    return labels


def priority_focus_sentence(ranking: List[Dict[str, Any]], fallback: str) -> str:
    rows = positive_impact_rows(ranking)
    if not rows:
        return fallback
    top = rows[0]
    return (
        f"Focus first on {top['name']}: raising it from {float(top['current_score']):.2f} "
        f"to {float(top['target_score']):.2f} is estimated to increase the predicted "
        f"employability score by {float(top['expected_gain']):.2f}."
    )


def priority_area_name(ranking: List[Dict[str, Any]], fallback: str) -> str:
    rows = positive_impact_rows(ranking)
    if not rows:
        return fallback
    return str(rows[0]["name"])


def trusted_learning_cards(selected_resources: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Keep only library links. The language model must not invent course URLs."""
    cards = []
    for resource in selected_resources or []:
        url = str(resource.get("url") or "")
        if not url.startswith("https://"):
            continue
        area = str(resource.get("area") or "Development area")
        provider = str(resource.get("provider") or "Trusted provider")
        cards.append(
            {
                "area": area,
                "provider": provider,
                "resource_type": str(resource.get("resource_type") or "Free learning source"),
                "topic": str(resource.get("topic") or "Learning resource"),
                "url": url,
                "reason": f"Trusted free source from {provider}, selected for {area}.",
            }
        )
    return cards


def impact_prompt_block(ranking: List[Dict[str, Any]]) -> str:
    if not ranking:
        return ""
    lines = [
        "Counterfactual impact from the frozen model "
        "(one construct raised to 4.00, every other construct unchanged):"
    ]
    for row in ranking:
        if row.get("already_at_target"):
            lines.append(
                f"- {row['name']}: already at or above 4.00, so this change is not a development priority."
            )
        else:
            lines.append(
                f"- {row['name']}: {float(row['current_score']):.2f} -> {float(row['target_score']):.2f} "
                f"changes the predicted score by {float(row['expected_gain']):+.4f}."
            )
    lines.append(
        "Order the Top 3 Areas for Improvement by the largest positive estimated gain. "
        "Do not rank a construct first only because its survey score is the lowest."
    )
    return "\n".join(lines)
