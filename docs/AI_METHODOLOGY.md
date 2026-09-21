# AI Methodology

All AI in DineSmart is **explainable and self-contained**: no external AI service, no API key, deterministic output that can be unit-tested and defended. Code lives in `backend/app/services/`.

## 1. Sentiment analysis (`sentiment.py`)

A lexicon-based analyser tuned for food reviews (~250 scored words and phrases, valence −3…+3).

- **Negation** ("not good") flips and softens a word; **intensifiers** ("very") and **dampeners** ("a bit") scale it; ALL-CAPS and `!` add emphasis; emoji are scored.
- **Contrast clauses**: text after "but/however" carries more weight ("tasty *but* slow").
- Clauses are split at commas so a negation never leaks across them.
- The sum is squashed to a −1…+1 compound score → `positive / negative / mixed / neutral`.
- The stored review sentiment blends **70 % text + 30 % star rating**.

**Dish- and aspect-level sentiment:** each review is scanned for ~150 dish names/synonyms (biryani, dosa, idli, pizza …), the restaurant's own menu items, and aspects (service, ambience, price, cleanliness, portion, wait time). Each mention gets the sentiment of *its own clause*, so "the biryani was great but the dosa was awful" yields biryani ▲ / dosa ▼. Lists ("The biryani, dosa and chutney were excellent") and follow-up sentences ("We ordered X. Both were amazing") inherit the opinion.

## 2. Review trust indicators (`trust.py`)

Score 0–100 starting at 60, with **every adjustment recorded as a human-readable reason**:

| Raises | Lowers |
|---|---|
| Detailed (15+/30+ words), mentions dishes, comments on service/price, balanced pros & cons | Very short, links/phone/email, all-caps, ≥4 `!`, repetitive wording, generic superlatives without specifics, promotional phrases, **star rating contradicting the text**, identical text in another review, burst of many reviews in an hour |

≥70 high · 45–69 medium · <45 low. **This flags patterns, it never declares a review fake**, and the UI says so. Low-trust reviews get a smaller weight (0.25–1.0) in the aggregated insights.

## 3. Restaurant insights (`insights.py`)

Trust-weighted positive %, overall label, best-rated dish (≥60 % positive), per-dish and per-aspect breakdown. **Confidence** is `low` (<3 reviews), `medium` (3–9), `high` (10+), and a plain-language message is shown when it is low.

## 4. Dietary evidence (`dietary.py`)

For each preference the best evidence wins: **verified** (OSM `diet:*` tag or menu-item flags) › **likely** (cuisine/name inference, e.g. Udupi, vegetarian cuisine) › **unknown** › **unlikely** (e.g. steak house for a vegetarian, "Non-Veg" in the name). Jain and gluten-free are *never* inferred from cuisine alone.

## 5. Recommender (`recommender.py`)

`match = 40·dietary fit + 20·quality + 20·taste affinity + 15·proximity + 5·information completeness`

- **Dietary fit** — mean and worst-case of the per-preference evidence (strict: one unsuitable preference drags the score down).
- **Quality** — Bayesian-smoothed rating (prior 3.6 worth 3 reviews), so one 5★ review does not beat forty 4.6★ ones; reduced when the reviews look untrustworthy.
- **Taste affinity** — cuisine overlap with places you saved (+1) or rated ≥4 (+0.7), minus places rated ≤2.
- **Proximity** — `exp(−km / 6)`.
- Output includes up to three reasons, a confidence level and a caution note (e.g. "May not suit Vegetarian: focuses on meat/seafood").

## Known limitations (be upfront in your report / viva)

- Lexicon sentiment can miss sarcasm and rare slang; a fine-tuned transformer would do better at the cost of size, speed and explainability.
- Dietary data depends on OpenStreetMap coverage, so many places are "unknown".
- Trust scoring is heuristic and has not been validated against labelled fake-review data.
- The recommender weights are hand-tuned, not learned.
