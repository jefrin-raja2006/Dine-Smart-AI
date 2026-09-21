"""Restaurant-level AI insights aggregated from analysed reviews.

Low-trust reviews count for less (weight 0.25 .. 1.0) so suspicious reviews
cannot easily swing the overall picture.
"""

import json

from app.models.models import Review
from app.services.trust import label_for_trust

MIN_REVIEWS_MEDIUM = 3
MIN_REVIEWS_HIGH = 10
BEST_DISH_MIN_POSITIVE = 60


def _weight(review: Review) -> float:
    trust = review.trust_score if review.trust_score is not None else 0.6
    return 0.25 + 0.75 * trust


def _mentions(review: Review) -> list[dict]:
    if not review.analysis_json:
        return []
    try:
        return json.loads(review.analysis_json).get("mentions", [])
    except ValueError:
        return []


def _aggregate(reviews: list[Review], kind: str) -> list[dict]:
    stats: dict[str, dict] = {}

    for review in reviews:
        weight = _weight(review)
        for mention in _mentions(review):
            if mention.get("kind") != kind:
                continue
            entry = stats.setdefault(
                mention["name"],
                {"mentions": 0, "pos": 0.0, "neg": 0.0},
            )
            entry["mentions"] += 1
            if mention["label"] == "positive":
                entry["pos"] += weight
            elif mention["label"] == "negative":
                entry["neg"] += weight

    result = []
    for name, entry in stats.items():
        opinion = entry["pos"] + entry["neg"]
        positive_pct = round(100 * entry["pos"] / opinion) if opinion else None

        if positive_pct is None:
            label = "neutral"
        elif positive_pct >= 65:
            label = "positive"
        elif positive_pct <= 35:
            label = "negative"
        else:
            label = "mixed"

        result.append(
            {
                "name": name,
                "mentions": entry["mentions"],
                "positive_pct": positive_pct,
                "label": label,
            }
        )

    result.sort(
        key=lambda d: (
            d["positive_pct"] if d["positive_pct"] is not None else -1,
            d["mentions"],
        ),
        reverse=True,
    )
    return result


def build_insights(reviews: list[Review]) -> dict:
    count = len(reviews)

    if count == 0:
        return {
            "review_count": 0,
            "average_rating": None,
            "confidence": "none",
            "message": "No reviews yet - be the first to share your experience.",
            "sentiment": None,
            "trust": None,
            "dishes": [],
            "aspects": [],
            "best_dish": None,
        }

    weights = [_weight(r) for r in reviews]
    total_weight = sum(weights)

    distribution = {"positive": 0, "mixed": 0, "negative": 0, "neutral": 0}
    for review in reviews:
        distribution[review.sentiment if review.sentiment in distribution else "neutral"] += 1

    positive_weight = sum(
        w for r, w in zip(reviews, weights) if r.sentiment == "positive"
    )
    positive_pct = round(100 * positive_weight / total_weight)

    mean_score = sum(
        (r.sentiment_score or 0.0) * w for r, w in zip(reviews, weights)
    ) / total_weight

    if mean_score >= 0.25:
        overall = "positive"
    elif mean_score <= -0.25:
        overall = "negative"
    else:
        overall = "mixed"

    trust_scores = [r.trust_score for r in reviews if r.trust_score is not None]
    avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0

    dishes = _aggregate(reviews, "dish")
    aspects = _aggregate(reviews, "aspect")

    best = next(
        (
            d for d in dishes
            if d["positive_pct"] is not None
            and d["positive_pct"] >= BEST_DISH_MIN_POSITIVE
        ),
        None,
    )

    if count >= MIN_REVIEWS_HIGH:
        confidence, message = "high", None
    elif count >= MIN_REVIEWS_MEDIUM:
        confidence, message = "medium", None
    else:
        confidence = "low"
        message = (
            f"Only {count} review{'s' if count != 1 else ''} so far - "
            "these insights are indicative, not conclusive."
        )

    return {
        "review_count": count,
        "average_rating": round(sum(r.rating for r in reviews) / count, 1),
        "confidence": confidence,
        "message": message,
        "sentiment": {
            "positive_pct": positive_pct,
            "label": overall,
            "distribution": distribution,
        },
        "trust": {
            "score": round(avg_trust * 100),
            "label": label_for_trust(avg_trust),
            "low_trust_reviews": sum(
                1 for s in trust_scores if label_for_trust(s) == "low"
            ),
        },
        "dishes": dishes,
        "aspects": aspects,
        "best_dish": best,
    }
