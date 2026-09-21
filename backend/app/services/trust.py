"""Review trust scoring.

IMPORTANT (also stated in the UI): this produces *indicators*, not verdicts.
A low trust score means "this review shows patterns that are common in
low-information or promotional reviews" - it never claims a review is fake.

Every deduction is returned as a human-readable reason so the score is
explainable to users and examiners.
"""

import re
from dataclasses import dataclass, field

from app.services.sentiment import ReviewSentiment

BASE_SCORE = 60

HIGH_THRESHOLD = 70
MEDIUM_THRESHOLD = 45

_URL_RE = re.compile(r"(https?://|www\.|\b[a-z0-9-]+\.(com|in|net|org|co)\b)", re.I)
_PHONE_RE = re.compile(r"(\+?\d[\d\s\-]{8,}\d)")
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
_WORD_RE = re.compile(r"[A-Za-z']+")

_GENERIC_SUPERLATIVES = {
    "best", "amazing", "awesome", "excellent", "perfect", "great",
    "fantastic", "wonderful", "superb", "outstanding", "worst", "terrible",
    "awful", "horrible",
}

_PROMO_PHRASES = (
    "must visit", "best in the world", "best restaurant ever", "highly recommended",
    "five star", "5 star", "visit us", "call us", "book now", "discount",
    "offer", "whatsapp",
)


@dataclass
class TrustContext:
    """Facts about the surrounding data the scorer can't see in the text."""

    duplicate_elsewhere: bool = False   # identical text posted by someone else
    recent_reviews_by_user: int = 0     # reviews by this user in the last hour


@dataclass
class TrustResult:
    score: float                          # 0.0 .. 1.0
    label: str                            # high | medium | low
    reasons: list[str] = field(default_factory=list)   # things that lowered it
    strengths: list[str] = field(default_factory=list)  # things that raised it


def label_for_trust(score: float) -> str:
    points = score * 100
    if points >= HIGH_THRESHOLD:
        return "high"
    if points >= MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def score_review(
    text: str,
    rating: int,
    sentiment: ReviewSentiment,
    context: TrustContext | None = None,
) -> TrustResult:
    context = context or TrustContext()

    points = BASE_SCORE
    reasons: list[str] = []
    strengths: list[str] = []

    words = _WORD_RE.findall(text)
    word_count = len(words)
    lowered = text.lower()

    # ---- length / detail --------------------------------------------
    if word_count < 4:
        points -= 25
        reasons.append("Very short review with little detail")
    elif word_count < 8:
        points -= 10
        reasons.append("Short review with limited detail")
    elif word_count >= 30:
        points += 15
        strengths.append("Detailed review")
    elif word_count >= 15:
        points += 10
        strengths.append("Reasonably detailed review")

    # ---- specificity ------------------------------------------------
    dishes = [m for m in sentiment.mentions if m.kind == "dish"]
    aspects = [m for m in sentiment.mentions if m.kind == "aspect"]

    if dishes:
        points += 10
        strengths.append("Mentions specific dishes")
    if aspects:
        points += 5
        strengths.append("Comments on service/ambience/price")

    # balanced opinions are a good sign of a genuine experience
    if sentiment.label == "mixed":
        points += 5
        strengths.append("Balanced (mentions positives and negatives)")

    # ---- generic hype without specifics -----------------------------
    superlatives = sum(1 for w in words if w.lower() in _GENERIC_SUPERLATIVES)
    if superlatives >= 2 and not dishes and not aspects:
        points -= 10
        reasons.append("Generic praise/criticism without specific details")

    if any(phrase in lowered for phrase in _PROMO_PHRASES):
        points -= 10
        reasons.append("Uses promotional-style wording")

    # ---- links / contact details ------------------------------------
    if _URL_RE.search(text) or _PHONE_RE.search(text) or _EMAIL_RE.search(text):
        points -= 25
        reasons.append("Contains links or contact details")

    # ---- shouting / excessive punctuation ---------------------------
    letters = [c for c in text if c.isalpha()]
    if len(letters) >= 12:
        caps_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if caps_ratio > 0.6:
            points -= 10
            reasons.append("Mostly written in capital letters")

    if text.count("!") >= 4:
        points -= 10
        reasons.append("Excessive exclamation marks")

    # ---- repetition -------------------------------------------------
    if word_count >= 8:
        unique_ratio = len({w.lower() for w in words}) / word_count
        if unique_ratio < 0.5:
            points -= 10
            reasons.append("Highly repetitive wording")

    # ---- rating vs. text disagreement -------------------------------
    if sentiment.score >= 0.5 and rating <= 2:
        points -= 25
        reasons.append("Star rating contradicts the positive text")
    elif sentiment.score <= -0.5 and rating >= 4:
        points -= 25
        reasons.append("Star rating contradicts the negative text")

    # ---- context from other reviews ---------------------------------
    if context.duplicate_elsewhere:
        points -= 30
        reasons.append("Identical text appears in another review")

    if context.recent_reviews_by_user >= 5:
        points -= 15
        reasons.append("Reviewer posted many reviews in a short time")

    points = max(0, min(100, points))
    score = round(points / 100, 2)

    return TrustResult(
        score=score,
        label=label_for_trust(score),
        reasons=reasons,
        strengths=strengths,
    )
