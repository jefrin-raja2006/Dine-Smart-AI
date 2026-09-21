"""Dietary suitability evidence for a restaurant.

For each dietary preference we answer: "how sure are we that this place suits
someone with this preference, and *why*?"

Levels
  verified  - stated explicitly (OpenStreetMap `diet:*` tag or menu data)
  likely    - inferred from cuisine / name (e.g. an Udupi or vegetarian place)
  unknown   - nothing to go on
  unlikely  - evidence against (e.g. a steak house for a vegetarian)

The app NEVER claims a dish is allergen-free; inferred results are labelled
"likely" and users are told to confirm with the restaurant.
"""

import json
import re
from dataclasses import dataclass

from app.constants import DIETARY_PREFERENCES

LEVEL_WEIGHT = {
    "verified": 1.0,
    "likely": 0.65,
    "unknown": 0.25,
    "unlikely": 0.0,
}

# OSM cuisine tokens
_VEG_POSITIVE_CUISINES = {
    "vegetarian", "vegan", "south_indian", "udupi", "gujarati", "rajasthani",
    "jain", "sattvic", "sattvik", "ice_cream", "dessert", "juice", "bakery",
    "tea", "coffee_shop", "sweets", "dosa", "idli", "salad",
}
_NONVEG_CUISINES = {
    "steak_house", "steak", "seafood", "fish", "chicken", "kebab", "meat",
    "fish_and_chips", "sushi", "ribs", "barbecue_meat", "hot_dog",
}
_VEGAN_CUISINES = {"vegan"}

_NON_VEG_NAME_RE = re.compile(r"\bnon[\s\-]*veg\b", re.I)
_VEG_NAME_RE = re.compile(
    r"\b(pure[\s\-]*veg(?:etarian)?|vegetarian|veg|sattvik|sattvic|udupi)\b", re.I
)
_VEGAN_NAME_RE = re.compile(r"\bvegan\b", re.I)
_JAIN_NAME_RE = re.compile(r"\bjain\b", re.I)

_YES = {"yes", "only"}


@dataclass
class DietEvidence:
    preference: str
    level: str          # verified | likely | unknown | unlikely
    source: str         # osm_tag | menu | cuisine | name | none
    note: str

    @property
    def weight(self) -> float:
        return LEVEL_WEIGHT[self.level]


def parse_diet_tags(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _cuisine_tokens(cuisine: str | None) -> set[str]:
    if not cuisine:
        return set()
    tokens = re.split(r"[;,/]+", cuisine.lower())
    return {re.sub(r"[\s\-]+", "_", t.strip()) for t in tokens if t.strip()}


def _osm_value(tags: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        if key in tags:
            return str(tags[key]).lower()
    return None


def _menu_evidence(preference: str, menu_items: list) -> DietEvidence | None:
    flag = {
        "Vegetarian": "is_vegetarian",
        "Vegan": "is_vegan",
        "Jain": "is_jain",
        "Gluten-Free": "is_gluten_free",
    }.get(preference)

    if not flag or not menu_items:
        return None

    total = len(menu_items)
    matching = sum(1 for item in menu_items if getattr(item, flag, False))

    if matching == 0:
        return None

    level = "verified" if matching / total >= 0.5 else "likely"

    return DietEvidence(
        preference,
        level,
        "menu",
        f"{matching} of {total} menu items are marked {preference.lower()}",
    )


def evidence_for(
    preference: str,
    *,
    name: str,
    cuisine: str | None,
    diet_tags: dict[str, str],
    menu_items: list | None = None,
) -> DietEvidence:
    """Best available evidence that `preference` suits this restaurant."""
    cuisines = _cuisine_tokens(cuisine)
    menu_items = menu_items or []

    candidates: list[DietEvidence] = []

    # ---- 1. explicit OpenStreetMap tags -----------------------------
    if preference == "Vegetarian":
        value = _osm_value(diet_tags, "vegetarian")
        # a vegan place is also vegetarian
        vegan_value = _osm_value(diet_tags, "vegan")
        if value in _YES or vegan_value == "only":
            candidates.append(DietEvidence(
                preference, "verified", "osm_tag",
                "Listed as vegetarian-friendly on OpenStreetMap"))
        elif value == "limited":
            candidates.append(DietEvidence(
                preference, "likely", "osm_tag",
                "Limited vegetarian options (OpenStreetMap)"))
        elif value == "no":
            candidates.append(DietEvidence(
                preference, "unlikely", "osm_tag",
                "OpenStreetMap says no vegetarian options"))

    elif preference == "Vegan":
        value = _osm_value(diet_tags, "vegan")
        if value in _YES:
            candidates.append(DietEvidence(
                preference, "verified", "osm_tag",
                "Listed as vegan-friendly on OpenStreetMap"))
        elif value == "limited":
            candidates.append(DietEvidence(
                preference, "likely", "osm_tag",
                "Limited vegan options (OpenStreetMap)"))
        elif value == "no":
            candidates.append(DietEvidence(
                preference, "unlikely", "osm_tag",
                "OpenStreetMap says no vegan options"))

    elif preference == "Gluten-Free":
        value = _osm_value(diet_tags, "gluten_free", "gluten-free")
        if value in _YES:
            candidates.append(DietEvidence(
                preference, "verified", "osm_tag",
                "Listed as gluten-free friendly on OpenStreetMap"))
        elif value == "limited":
            candidates.append(DietEvidence(
                preference, "likely", "osm_tag",
                "Limited gluten-free options (OpenStreetMap)"))
        elif value == "no":
            candidates.append(DietEvidence(
                preference, "unlikely", "osm_tag",
                "OpenStreetMap says no gluten-free options"))

    elif preference == "Jain":
        value = _osm_value(diet_tags, "jain")
        if value in _YES:
            candidates.append(DietEvidence(
                preference, "verified", "osm_tag",
                "Listed as Jain-friendly on OpenStreetMap"))

    elif preference == "Dairy-Free":
        value = _osm_value(diet_tags, "lactose_free", "dairy_free", "lactose-free")
        if value in _YES:
            candidates.append(DietEvidence(
                preference, "verified", "osm_tag",
                "Listed as dairy/lactose-free on OpenStreetMap"))
        elif _osm_value(diet_tags, "vegan") in _YES:
            candidates.append(DietEvidence(
                preference, "likely", "osm_tag",
                "Vegan-friendly places usually avoid dairy"))

    # ---- 2. menu data -----------------------------------------------
    menu = _menu_evidence(preference, menu_items)
    if menu:
        candidates.append(menu)

    # ---- 3. cuisine / name inference --------------------------------
    is_non_veg_name = bool(_NON_VEG_NAME_RE.search(name or ""))

    if preference == "Vegetarian":
        if cuisines & {"vegetarian", "vegan"}:
            candidates.append(DietEvidence(
                preference, "likely", "cuisine", "Vegetarian cuisine"))
        elif not is_non_veg_name and _VEG_NAME_RE.search(name or ""):
            candidates.append(DietEvidence(
                preference, "likely", "name", "Name suggests a vegetarian place"))
        elif cuisines & _VEG_POSITIVE_CUISINES and not cuisines & _NONVEG_CUISINES:
            candidates.append(DietEvidence(
                preference, "likely", "cuisine",
                "Cuisine is typically vegetarian-friendly"))
        elif is_non_veg_name or cuisines & _NONVEG_CUISINES:
            candidates.append(DietEvidence(
                preference, "unlikely", "cuisine",
                "Focuses on meat/seafood"))

    elif preference == "Vegan":
        if cuisines & _VEGAN_CUISINES:
            candidates.append(DietEvidence(
                preference, "likely", "cuisine", "Vegan cuisine"))
        elif _VEGAN_NAME_RE.search(name or ""):
            candidates.append(DietEvidence(
                preference, "likely", "name", "Name suggests a vegan place"))
        elif is_non_veg_name or cuisines & _NONVEG_CUISINES:
            candidates.append(DietEvidence(
                preference, "unlikely", "cuisine", "Focuses on meat/seafood"))

    elif preference == "Jain":
        if _JAIN_NAME_RE.search(name or "") or "jain" in cuisines:
            candidates.append(DietEvidence(
                preference, "likely", "name", "Name/cuisine suggests Jain food"))
        elif is_non_veg_name or cuisines & _NONVEG_CUISINES:
            candidates.append(DietEvidence(
                preference, "unlikely", "cuisine", "Focuses on meat/seafood"))

    elif preference == "Dairy-Free":
        if cuisines & _VEGAN_CUISINES:
            candidates.append(DietEvidence(
                preference, "likely", "cuisine", "Vegan cuisine is dairy-free"))

    if not candidates:
        return DietEvidence(preference, "unknown", "none", "No dietary information available")

    # Positive evidence beats negative; stronger beats weaker.
    positives = [c for c in candidates if c.level in ("verified", "likely")]
    if positives:
        return max(positives, key=lambda c: c.weight)

    return candidates[0]


def evaluate_all(
    *,
    name: str,
    cuisine: str | None,
    diet_tags: dict[str, str],
    menu_items: list | None = None,
) -> dict[str, DietEvidence]:
    return {
        preference: evidence_for(
            preference,
            name=name,
            cuisine=cuisine,
            diet_tags=diet_tags,
            menu_items=menu_items,
        )
        for preference in DIETARY_PREFERENCES
    }


def diet_labels(evidence: dict[str, DietEvidence]) -> list[dict]:
    """Compact list for the UI: only preferences with positive evidence."""
    return [
        {"name": e.preference, "level": e.level, "note": e.note}
        for e in evidence.values()
        if e.level in ("verified", "likely")
    ]
