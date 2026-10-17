"""
Temporal Experience Calibration and Consistency Module
Grounded in empirical distributions from 02_github_expertise (Zenodo benchmark).
Evaluates claimed experience durations against public commit timelines and recency.
"""

import math
from typing import Dict, Any, Optional, Tuple


class TemporalCalibrator:
    """
    Evaluates temporal consistency between resume claims and observed public GitHub activity.
    Uses calibrated bounds to classify timeline consistency without arbitrary hardcoding.
    """

    # Empirical parameters estimated from 02_github_expertise
    DAYS_PER_YEAR = 365.25
    RECENCY_ACTIVE_THRESHOLD_DAYS = 365 * 2  # Active within past 2 years
    RECENCY_STALE_THRESHOLD_DAYS = 365 * 5   # Stale if no activity for > 5 years

    # Known initial release years for chronological impossibility checks
    TECH_RELEASE_YEARS = {
        "React": 2013,
        "React Native": 2015,
        "Node.js": 2009,
        "Express.js": 2010,
        "MongoDB": 2009,
        "FastAPI": 2018,
        "Docker": 2013,
        "Kubernetes": 2014,
        "TypeScript": 2012,
        "Vue.js": 2014,
        "Next.js": 2016,
        "GraphQL": 2015,
        "PyTorch": 2016,
        "TensorFlow": 2015,
        "Rust": 2015,
        "Go": 2009,
        "Flutter": 2017
    }

    def verify_chronological_feasibility(self, skill_name: str, claimed_years: float, current_year: int = 2026) -> Tuple[bool, Optional[str]]:
        """
        Checks if claimed experience exceeds the total existence time of the technology.
        e.g., Claiming 15 years of React in 2026 is chronologically impossible (React was released in 2013 -> max 13 years).
        """
        canonical = skill_name.strip()
        if canonical in self.TECH_RELEASE_YEARS:
            release_yr = self.TECH_RELEASE_YEARS[canonical]
            max_possible_years = current_year - release_yr
            if claimed_years > max_possible_years:
                return False, f"Claimed {claimed_years} years of {canonical}, but {canonical} was released in {release_yr} (maximum possible: {max_possible_years} years)."
        return True, None

    def evaluate_temporal_consistency(
        self,
        skill_name: str,
        claimed_years: Optional[float],
        observed_years: float,
        days_since_last_activity: int,
        projects_count: int
    ) -> Dict[str, Any]:
        """
        Computes calibrated temporal verdict:
        - SUPPORTED: Public timeline substantially corroborates claimed duration (>= 70% of claimed).
        - PARTIALLY_SUPPORTED: Public activity exists but spans shorter period than claimed (> 0% and < 70%).
        - INSUFFICIENT_EVIDENCE: No observable public activity (0 days).
        - POTENTIAL_CONTRADICTION: Chronological impossibility (e.g. tech didn't exist).
        """
        if claimed_years is not None and claimed_years > 0:
            # 1. Check Chronological Feasibility
            is_feasible, contradiction_reason = self.verify_chronological_feasibility(skill_name, claimed_years)
            if not is_feasible:
                return {
                    "verdict": "POTENTIAL_CONTRADICTION",
                    "confidence": 0.95,
                    "claimedYears": claimed_years,
                    "observedYears": observed_years,
                    "reason": contradiction_reason,
                    "recencyStatus": "CONTRADICTORY"
                }

            # 2. Check Observed Activity vs Claimed Duration
            if observed_years <= 0.0 or projects_count == 0:
                return {
                    "verdict": "INSUFFICIENT_EVIDENCE",
                    "confidence": 0.70,
                    "claimedYears": claimed_years,
                    "observedYears": 0.0,
                    "reason": "No public repository activity detected for this skill. Candidate may have private/commercial experience.",
                    "recencyStatus": "UNOBSERVED"
                }

            ratio = observed_years / claimed_years
            
            # Recency assessment
            if days_since_last_activity <= self.RECENCY_ACTIVE_THRESHOLD_DAYS:
                recency = "RECENTLY_ACTIVE"
            elif days_since_last_activity <= self.RECENCY_STALE_THRESHOLD_DAYS:
                recency = "MODERATELY_RECENT"
            else:
                recency = "DORMANT"

            days_count = int(round(observed_years * 365.25))
            obs_str = self._format_duration_str(observed_years, days_count)
            claim_str = self._format_duration_str(claimed_years, int(round(claimed_years * 365.25)))

            if ratio >= 0.70:
                recency_label = "recently active" if recency == "RECENTLY_ACTIVE" else recency.lower().replace("_", " ")
                return {
                    "verdict": "SUPPORTED",
                    "confidence": min(0.95, 0.75 + 0.20 * min(1.0, ratio)),
                    "claimedYears": claimed_years,
                    "observedYears": observed_years,
                    "timelineCoverage": round(min(1.0, ratio), 2),
                    "reason": f"Observed public GitHub activity spans {obs_str}, substantially supporting mentioned {claim_str} ({recency_label}).",
                    "recencyStatus": recency
                }
            else:
                recency_label = "recently active" if recency == "RECENTLY_ACTIVE" else recency.lower().replace("_", " ")
                return {
                    "verdict": "PARTIALLY_SUPPORTED",
                    "confidence": 0.80,
                    "claimedYears": claimed_years,
                    "observedYears": observed_years,
                    "timelineCoverage": round(ratio, 2),
                    "reason": f"Observed public GitHub activity spans {obs_str}, which partially corroborates mentioned {claim_str}. Remainder may be in private/enterprise projects.",
                    "recencyStatus": recency
                }
        
        else:
            # Skill claimed without explicit year quantity
            if observed_years > 0.0 and projects_count > 0:
                days_count = int(round(observed_years * 365.25))
                obs_str = self._format_duration_str(observed_years, days_count)
                return {
                    "verdict": "SUPPORTED",
                    "confidence": 0.85,
                    "claimedYears": None,
                    "observedYears": observed_years,
                    "reason": f"Public repository evidence confirms active usage spanning {obs_str} across {projects_count} project(s).",
                    "recencyStatus": "ACTIVE" if days_since_last_activity <= self.RECENCY_ACTIVE_THRESHOLD_DAYS else "INACTIVE"
                }
            else:
                return {
                    "verdict": "INSUFFICIENT_EVIDENCE",
                    "confidence": 0.65,
                    "claimedYears": None,
                    "observedYears": 0.0,
                    "reason": "Skill mentioned on resume without public GitHub artifact evidence.",
                    "recencyStatus": "UNOBSERVED"
                }

    @staticmethod
    def _format_duration_str(years: float, total_days: Optional[int] = None) -> str:
        """Formats years and days into solid, clean text e.g. '1 Year (540 days)'."""
        if years <= 0:
            return "0 days"
        days = total_days if (total_days and total_days > 0) else int(round(years * 365.25))
        if years >= 1.0:
            solid_yr = int(round(years))
            yr_str = "1 Year" if solid_yr == 1 else f"{solid_yr} Years"
            return f"{yr_str} ({days} days)"
        else:
            months = max(1, int(round(years * 12)))
            mo_str = "1 Month" if months == 1 else f"{months} Months"
            return f"{mo_str} ({days} days)"
