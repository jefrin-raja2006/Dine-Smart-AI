import pytest

from app.services.sentiment import analyze_text, blend_with_rating


def mention(result, name):
    return next(m for m in result.mentions if m.name == name)


@pytest.mark.parametrize(
    "text,label",
    [
        ("The biryani was excellent and the service was really good.", "positive"),
        ("Terrible experience. Cold food, rude staff and dirty tables.", "negative"),
        ("Not good at all. Not worth the money.", "negative"),
        ("Not bad, pretty decent for the price.", "positive"),
        ("Ordered a pizza. It arrived.", "neutral"),
        ("AMAZING food!!! Best paneer tikka ever 😍", "positive"),
    ],
)
def test_review_labels(text, label):
    assert analyze_text(text).label == label


def test_words_ending_in_nt_are_not_negations():
    assert analyze_text("The restaurant was excellent").label == "positive"


def test_negation_flips_sentiment():
    assert analyze_text("The food was good").score > 0
    assert analyze_text("The food was not good").score < 0


def test_intensifier_increases_strength():
    assert analyze_text("very good").score > analyze_text("good").score


def test_but_clause_weights_later_part():
    assert analyze_text("Tasty food but terrible service").score < 0


def test_mixed_review_detected():
    result = analyze_text("The food was amazing but the service was awful and slow")
    assert result.positive_sum > 1.5 and result.negative_sum > 1.5


def test_dish_level_sentiment_split_by_but():
    result = analyze_text("The biryani was great but the dosa was awful.")
    assert mention(result, "biryani").label == "positive"
    assert mention(result, "dosa").label == "negative"


def test_dish_level_split_on_comma():
    result = analyze_text("Cold coffee was great, burger was a bit dry though.")
    assert mention(result, "coffee").label == "positive"
    assert mention(result, "burger").label == "negative"


def test_dish_list_shares_opinion():
    result = analyze_text("The biryani, dosa and chutney were excellent.")
    assert {m.name for m in result.mentions} == {"biryani", "dosa", "chutney"}
    assert all(m.label == "positive" for m in result.mentions)


def test_neutral_mention_inherits_from_next_sentence():
    result = analyze_text("We ordered biryani and dosa. Both were amazing!")
    assert mention(result, "biryani").label == "positive"
    assert mention(result, "dosa").label == "positive"


def test_aspects_detected():
    m = mention(analyze_text("The service was very slow."), "service")
    assert m.kind == "aspect" and m.label == "negative"


def test_plural_and_synonym_dishes():
    names = {m.name for m in analyze_text("Loved the dosais and idlis").mentions}
    assert {"dosa", "idli"} <= names


def test_menu_item_names_are_recognised():
    result = analyze_text("The Chettinad Special was fantastic", ["Chettinad Special"])
    assert mention(result, "chettinad special").label == "positive"


def test_empty_text_is_safe():
    result = analyze_text("")
    assert result.label == "neutral" and result.mentions == []


def test_rating_blend():
    assert blend_with_rating(0.0, 5) > 0
    assert blend_with_rating(0.0, 1) < 0
    assert blend_with_rating(0.5, None) == 0.5
