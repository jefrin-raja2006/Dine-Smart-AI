from app.services.sentiment import analyze_text
from app.services.trust import TrustContext, score_review


def trust(text, rating, **ctx):
    return score_review(text, rating, analyze_text(text), TrustContext(**ctx))


def test_detailed_specific_review_is_high_trust():
    result = trust(
        "Loved the dosa, crispy and fresh. The sambar could have been hotter "
        "but the staff were friendly and the bill was reasonable.",
        4,
    )
    assert result.label == "high"
    assert result.strengths


def test_very_short_review_is_low_trust():
    result = trust("Good food", 5)
    assert result.label == "low"
    assert any("short" in r.lower() for r in result.reasons)


def test_promotional_spam_scores_very_low():
    result = trust("BEST RESTAURANT EVER!!!!! MUST VISIT!!! call us 9876543210", 5)
    assert result.score <= 0.1
    assert len(result.reasons) >= 3


def test_rating_text_contradiction_penalised():
    result = trust("The food was terrible and the service was awful, never coming back.", 5)
    assert any("contradicts" in r for r in result.reasons)


def test_duplicate_text_penalised():
    text = "Nice place with good food and friendly staff overall"
    assert trust(text, 4, duplicate_elsewhere=True).score < trust(text, 4).score


def test_review_burst_penalised():
    text = "Nice place with good food and friendly staff overall"
    assert trust(text, 4, recent_reviews_by_user=6).score < trust(text, 4).score


def test_repetitive_generic_review_penalised():
    assert trust("great great great great great great great great", 5).label == "low"


def test_score_is_clamped():
    result = trust("!!!! CALL 9876543210 www.spam.com BEST BEST", 5, duplicate_elsewhere=True)
    assert 0.0 <= result.score <= 1.0
