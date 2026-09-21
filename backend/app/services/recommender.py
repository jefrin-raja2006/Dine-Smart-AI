"""Explainable restaurant recommender.

Score (0-100) = weighted blend of five transparent components:

  dietary fit   40  how well the place matches the user's preferences
  quality       20  Bayesian-smoothed rating (few reviews are pulled to average)
  affinity      20  similarity to cuisines the user saved / rated highly
  proximity     15  closer is better (exponential decay, ~6 km scale)
  information    5  restaurants with contact/opening data are more useful

Each recommendation carries plain-language `reasons`, a `confidence` level
and (when evidence is thin) a fallback `note` - so users can see *why* and how
much to trust it.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass, field

from app.services.dietary import DietEvidence

W_DIET, W_QUALITY, W_AFFINITY, W_PROXIMITY, W_INFO = 40, 20, 20, 15, 5

PRIOR_RATING = 3.6      # assumed average rating for a place with no reviews
PRIOR_WEIGHT = 3        # ... worth this many reviews
PROXIMITY_SCALE_KM = 6.0
NEUTRAL_AFFINITY = 0.3

_GENERIC_TOKENS = {"restaurant", "food", "cafe", "fast_food", "food_court", ""}


@dataclass
class Candidate:
    id: int
    name: str
    cuisine: str | None
    distance_km: float | None
    rating: float | None
    review_count: int
    avg_trust: float | None
    has_address: bool
    has_contact: bool
    has_hours: bool
    evidence: dict[str, DietEvidence]
    best_dish: str | None = None


@dataclass
class UserProfile:
    preferences: list[str] = field(default_factory=list)
    affinity: Counter = field(default_factory=Counter)
    has_history: bool = False


@dataclass
class Recommendation:
    match: int
    reasons: list[str]
    confidence: str
    note: str | None
    components: dict[str, float]


def cuisine_tokens(cuisine: str | None) -> set[str]:
    if not cuisine:
        return set()
    tokens = re.split(r"[;,/]+", cuisine.lower())
    cleaned = {re.sub(r"[\s\-]+", "_", t.strip()) for t in tokens}
    return {t for t in cleaned if t not in _GENERIC_TOKENS}


def build_profile(
    preferences: list[str],
    favorite_cuisines: list[str | None],
    liked_cuisines: list[str | None],
    disliked_cuisines: list[str | None],
) -> UserProfile:
    affinity: Counter = Counter()

    for cuisine in favorite_cuisines:
        for token in cuisine_tokens(cuisine):
            affinity[token] += 1.0
    for cuisine in liked_cuisines:
        for token in cuisine_tokens(cuisine):
            affinity[token] += 0.7
    for cuisine in disliked_cuisines:
        for token in cuisine_tokens(cuisine):
            affinity[token] -= 0.7

    return UserProfile(
        preferences=list(preferences),
        affinity=affinity,
        has_history=bool(favorite_cuisines or liked_cuisines or disliked_cuisines),
    )


def _diet_fit(candidate: Candidate, profile: UserProfile) -> float:
    if not profile.preferences:
        return 0.5

    weights = [candidate.evidence[p].weight for p in profile.preferences]
    # strict: one unsuitable preference drags the whole fit down
    return 0.5 * (sum(weights) / len(weights)) + 0.5 * min(weights)


def _quality(candidate: Candidate) -> float:
    count = candidate.review_count
    rating = candidate.rating or 0.0
    smoothed = (count * rating + PRIOR_WEIGHT * PRIOR_RATING) / (count + PRIOR_WEIGHT)
    quality = (smoothed - 1) / 4

    if count >= 2 and candidate.avg_trust is not None and candidate.avg_trust < 0.45:
        quality *= 0.7

    return max(0.0, min(1.0, quality))


def _affinity(candidate: Candidate, profile: UserProfile) -> tuple[float, list[str]]:
    if not profile.has_history:
        return NEUTRAL_AFFINITY, []

    shared = [
        t for t in cuisine_tokens(candidate.cuisine) if profile.affinity.get(t, 0) > 0
    ]
    raw = sum(profile.affinity.get(t, 0) for t in cuisine_tokens(candidate.cuisine))

    return max(0.0, min(1.0, raw / 2)), shared


def _proximity(candidate: Candidate) -> float:
    if candidate.distance_km is None:
        return 0.5
    return math.exp(-candidate.distance_km / PROXIMITY_SCALE_KM)


def _information(candidate: Candidate) -> float:
    return (
        0.4 * candidate.has_contact
        + 0.3 * candidate.has_hours
        + 0.3 * candidate.has_address
    )


def score_candidate(candidate: Candidate, profile: UserProfile) -> Recommendation:
    fit = _diet_fit(candidate, profile)
    quality = _quality(candidate)
    affinity, shared = _affinity(candidate, profile)
    proximity = _proximity(candidate)
    info = _information(candidate)

    total = (
        W_DIET * fit
        + W_QUALITY * quality
        + W_AFFINITY * affinity
        + W_PROXIMITY * proximity
        + W_INFO * info
    )

    # ---- explanation -------------------------------------------------
    reasons: list[str] = []
    warnings: list[str] = []

    for preference in profile.preferences:
        evidence = candidate.evidence[preference]
        if evidence.level == "verified":
            reasons.append(f"{preference}: {evidence.note}")
        elif evidence.level == "likely":
            reasons.append(f"{preference} (likely): {evidence.note}")
        elif evidence.level == "unlikely":
            warnings.append(f"May not suit {preference}: {evidence.note}")

    if shared:
        pretty = ", ".join(t.replace("_", " ").title() for t in shared[:2])
        reasons.append(f"Serves {pretty}, like places you saved")

    if candidate.review_count and (candidate.rating or 0) >= 4:
        reasons.append(
            f"Rated {candidate.rating:.1f}\u2605 by "
            f"{candidate.review_count} reviewer"
            f"{'s' if candidate.review_count != 1 else ''}"
        )

    if candidate.distance_km is not None and candidate.distance_km <= 2:
        if candidate.distance_km < 0.1:
            reasons.append("Right next to you")
        else:
            reasons.append(f"Only {candidate.distance_km:.1f} km away")

    # ---- confidence & fallback note ---------------------------------
    levels = [candidate.evidence[p].level for p in profile.preferences]

    if profile.preferences:
        if any(level == "unlikely" for level in levels):
            confidence = "low"
        elif all(level == "verified" for level in levels):
            confidence = "high"
        elif any(level in ("verified", "likely") for level in levels):
            confidence = "medium"
        else:
            confidence = "low"
    else:
        confidence = (
            "high" if candidate.review_count >= 3
            else "medium" if candidate.review_count >= 1
            else "low"
        )

    note = None
    if warnings:
        note = warnings[0]
    elif profile.preferences and confidence in ("low", "medium") and not all(
        level == "verified" for level in levels
    ):
        note = (
            "Dietary details are not fully verified - "
            "please confirm with the restaurant."
        )

    return Recommendation(
        match=max(0, min(100, round(total))),
        reasons=reasons[:3],
        confidence=confidence,
        note=note,
        components={
            "dietary_fit": round(W_DIET * fit, 1),
            "quality": round(W_QUALITY * quality, 1),
            "affinity": round(W_AFFINITY * affinity, 1),
            "proximity": round(W_PROXIMITY * proximity, 1),
            "information": round(W_INFO * info, 1),
        },
    )
