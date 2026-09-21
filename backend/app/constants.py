import re

# Canonical dietary preference names (what the UI shows / the DB stores).
DIETARY_PREFERENCES = [
    "Vegetarian",
    "Vegan",
    "Jain",
    "Gluten-Free",
    "Dairy-Free",
]

_LOOKUP = {
    re.sub(r"[\s_\-]+", "", name.lower()): name for name in DIETARY_PREFERENCES
}


def normalize_preference(name: str) -> str | None:
    """'gluten free' / 'GLUTEN_FREE' -> 'Gluten-Free'. Unknown names -> None."""
    if not isinstance(name, str):
        return None
    key = re.sub(r"[\s_\-]+", "", name.strip().lower())
    return _LOOKUP.get(key)


def normalize_preferences(names: list[str]) -> tuple[list[str], list[str]]:
    """Return (valid canonical names without duplicates, invalid inputs)."""
    valid: list[str] = []
    invalid: list[str] = []
    for raw in names:
        if not isinstance(raw, str) or not raw.strip():
            continue
        canonical = normalize_preference(raw)
        if canonical is None:
            invalid.append(raw)
        elif canonical not in valid:
            valid.append(canonical)
    return valid, invalid
