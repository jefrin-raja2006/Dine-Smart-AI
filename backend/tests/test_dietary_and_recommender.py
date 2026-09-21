from types import SimpleNamespace

from app.services import dietary
from app.services.recommender import Candidate, build_profile, score_candidate


def ev(pref, name="Place", cuisine=None, tags=None, menu=None):
    return dietary.evidence_for(
        pref, name=name, cuisine=cuisine, diet_tags=tags or {}, menu_items=menu
    )


def test_osm_tag_is_verified():
    assert ev("Vegetarian", tags={"vegetarian": "only"}).level == "verified"
    assert ev("Gluten-Free", tags={"gluten_free": "yes"}).level == "verified"


def test_explicit_no_is_unlikely():
    assert ev("Vegan", tags={"vegan": "no"}).level == "unlikely"


def test_cuisine_inference_is_only_likely():
    assert ev("Vegetarian", cuisine="South Indian").level == "likely"


def test_meat_focused_is_unlikely_for_vegetarian():
    assert ev("Vegetarian", cuisine="Steak House").level == "unlikely"
    assert ev("Vegetarian", name="Royal Non-Veg Corner").level == "unlikely"


def test_name_hint_but_not_non_veg():
    assert ev("Vegetarian", name="Pure Veg Bhavan").level == "likely"


def test_jain_never_inferred_from_generic_vegetarian():
    assert ev("Jain", cuisine="South Indian").level == "unknown"


def test_unknown_when_no_info():
    assert ev("Gluten-Free").level == "unknown"


def test_menu_items_provide_evidence():
    menu = [SimpleNamespace(is_vegetarian=True), SimpleNamespace(is_vegetarian=True),
            SimpleNamespace(is_vegetarian=False)]
    e = ev("Vegetarian", menu=menu)
    assert e.level == "verified" and e.source == "menu"


def test_vegan_implies_dairy_free_likely():
    assert ev("Dairy-Free", tags={"vegan": "yes"}).level == "likely"


def candidate(name="X", cuisine="Indian", tags=None, **kw):
    evidence = dietary.evaluate_all(
        name=name, cuisine=cuisine, diet_tags=tags or {}, menu_items=None
    )
    base = dict(
        id=1, name=name, cuisine=cuisine, distance_km=1.0, rating=None,
        review_count=0, avg_trust=None, has_address=True, has_contact=False,
        has_hours=False, evidence=evidence,
    )
    base.update(kw)
    return Candidate(**base)


def profile(prefs=(), fav=(), liked=(), disliked=()):
    return build_profile(list(prefs), list(fav), list(liked), list(disliked))


def test_verified_diet_match_outranks_unknown():
    p = profile(["Vegetarian"])
    good = score_candidate(candidate(tags={"vegetarian": "only"}), p)
    unknown = score_candidate(candidate(), p)
    assert good.match > unknown.match
    assert good.confidence == "high"
    assert unknown.confidence == "low" and unknown.note


def test_unsuitable_place_gets_warning():
    rec = score_candidate(candidate(cuisine="Steak House"), profile(["Vegetarian"]))
    assert rec.confidence == "low"
    assert "May not suit Vegetarian" in rec.note


def test_strict_diets_one_failure_drags_down():
    p = profile(["Vegetarian", "Gluten-Free"])
    both = score_candidate(candidate(tags={"vegetarian": "yes", "gluten_free": "yes"}), p)
    one = score_candidate(candidate(tags={"vegetarian": "yes"}), p)
    assert both.match > one.match


def test_closer_is_better():
    p = profile()
    assert score_candidate(candidate(distance_km=0.5), p).match > \
        score_candidate(candidate(distance_km=12), p).match


def test_few_reviews_are_smoothed():
    p = profile()
    one_perfect = score_candidate(candidate(rating=5.0, review_count=1), p)
    many_great = score_candidate(candidate(rating=4.6, review_count=40), p)
    assert many_great.match >= one_perfect.match


def test_low_trust_reviews_reduce_quality():
    p = profile()
    trusted = score_candidate(candidate(rating=4.8, review_count=5, avg_trust=0.9), p)
    shady = score_candidate(candidate(rating=4.8, review_count=5, avg_trust=0.2), p)
    assert trusted.match > shady.match


def test_affinity_from_favorites():
    p = profile(fav=["Chinese"])
    chinese = score_candidate(candidate(cuisine="Chinese"), p)
    italian = score_candidate(candidate(cuisine="Italian"), p)
    assert chinese.match > italian.match
    assert any("Chinese" in r for r in chinese.reasons)


def test_score_bounds():
    assert 0 <= score_candidate(candidate(), profile()).match <= 100
