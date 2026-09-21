"""Explainable, lexicon-based sentiment analysis for restaurant reviews.

Why lexicon-based (rather than a downloaded ML model)?
  * deterministic and fully unit-testable,
  * no model download, GPU or extra dependency to deploy,
  * every score can be explained ("loved" +2.5, "slow" -1.6 ...).

What it does
  1. Tokenises the review and scores words from a food/service-specific
     lexicon, handling negation ("not good"), intensifiers ("very good"),
     dampeners ("a bit slow"), CAPS emphasis and "but" clauses
     ("tasty but slow" -> the part after "but" matters more).
  2. Produces a review-level label: positive / negative / mixed / neutral.
  3. Finds *dish* mentions (biryani, dosa ...) and *aspect* mentions
     (service, ambience, price, cleanliness) and scores the sentiment of the
     clause each one appears in -> dish-level insights.
"""

import math
import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# LEXICON  (valence: -3 very negative ... +3 very positive)
# ---------------------------------------------------------------------------

POSITIVE = {
    # general praise
    "excellent": 3.0, "amazing": 3.0, "awesome": 3.0, "fantastic": 3.0,
    "outstanding": 3.0, "superb": 3.0, "perfect": 3.0, "perfectly": 2.5,
    "wonderful": 2.8, "brilliant": 2.8, "incredible": 2.8, "phenomenal": 3.0,
    "delightful": 2.5, "exceptional": 3.0, "heavenly": 3.0, "divine": 2.8,
    "great": 2.5, "love": 2.5, "loved": 2.5, "loves": 2.5, "loving": 2.0,
    "best": 2.8, "favorite": 2.3, "favourite": 2.3, "fabulous": 2.8,
    "good": 1.8, "nice": 1.5, "lovely": 2.2, "pleasant": 1.8, "enjoy": 2.0,
    "enjoyed": 2.0, "enjoyable": 2.0, "happy": 1.8, "pleased": 1.8,
    "impressed": 2.2, "impressive": 2.2, "satisfying": 2.0, "satisfied": 1.8,
    "recommend": 2.0, "recommended": 2.0, "recommends": 2.0,
    "worth": 1.5, "worthy": 1.5, "wow": 2.0, "yum": 2.2, "yummy": 2.2,
    "decent": 1.0, "fine": 0.4, "okay": 0.3, "ok": 0.3, "alright": 0.3,
    "top": 1.2, "superior": 2.0, "premium": 1.2, "class": 0.8,
    # food quality
    "delicious": 2.8, "tasty": 2.2, "flavorful": 2.2, "flavourful": 2.2,
    "flavour": 0.8, "flavor": 0.8, "authentic": 1.6, "fresh": 1.6,
    "freshly": 1.5, "crispy": 1.6, "crisp": 1.4, "juicy": 1.8,
    "tender": 1.8, "soft": 1.0, "fluffy": 1.6, "creamy": 1.4, "rich": 1.0,
    "aromatic": 1.8, "mouthwatering": 2.8, "scrumptious": 2.8,
    "wholesome": 1.6, "generous": 1.6, "filling": 1.0, "balanced": 1.2,
    "well-cooked": 1.8, "spot-on": 2.0, "spoton": 2.0, "unique": 1.2,
    "healthy": 1.4, "hearty": 1.6, "tangy": 1.0, "melts": 1.5,
    # service / place
    "friendly": 1.8, "polite": 1.6, "courteous": 1.8, "welcoming": 1.8,
    "attentive": 1.8, "helpful": 1.6, "quick": 1.3, "fast": 1.3,
    "prompt": 1.6, "efficient": 1.4, "clean": 1.6, "hygienic": 2.0,
    "spotless": 2.2, "cozy": 1.6, "cosy": 1.6, "comfortable": 1.5,
    "spacious": 1.2, "beautiful": 1.8, "peaceful": 1.4, "vibrant": 1.2,
    "affordable": 1.4, "reasonable": 1.2, "cheap": 0.6, "value": 1.0,
    "professional": 1.4, "warm": 1.0, "smiling": 1.2,
}

NEGATIVE = {
    # general criticism
    "terrible": -3.0, "awful": -3.0, "horrible": -3.0, "worst": -3.0,
    "disgusting": -3.0, "horrendous": -3.0, "appalling": -3.0,
    "pathetic": -2.8, "dreadful": -2.8, "nasty": -2.6, "bad": -2.0,
    "poor": -2.0, "worse": -2.4, "unacceptable": -2.6, "avoid": -2.5,
    "hate": -2.6, "hated": -2.6, "disappointing": -2.5, "disappointed": -2.5,
    "disappointment": -2.5, "mediocre": -1.5, "meh": -1.2, "average": -0.6,
    "overrated": -2.0, "waste": -2.2, "wasted": -2.2, "regret": -2.2,
    "regretted": -2.2, "unhappy": -2.0, "annoying": -1.8, "annoyed": -1.8,
    "complaint": -1.2, "complaints": -1.2, "issue": -0.8, "issues": -0.8,
    "problem": -1.0, "problems": -1.0, "mistake": -1.2, "lacking": -1.5,
    "lacks": -1.5, "lacked": -1.5, "sad": -1.5, "upset": -1.8,
    # food quality
    "bland": -2.0, "tasteless": -2.6, "stale": -2.6, "rotten": -3.0,
    "raw": -1.5, "undercooked": -2.5, "overcooked": -2.0, "burnt": -2.0,
    "burned": -2.0, "greasy": -1.6, "oily": -1.3, "soggy": -2.0,
    "salty": -0.8, "dry": -1.4, "hard": -0.8, "chewy": -1.6, "tough": -1.4,
    "spoiled": -3.0, "smelly": -2.2, "stinking": -2.6, "sour": -1.0,
    "watery": -1.6, "flavourless": -2.4, "flavorless": -2.4, "cold": -1.3,
    "expired": -3.0, "hair": -1.5, "insect": -2.8, "cockroach": -3.0,
    "roach": -3.0, "fly": -0.8, "flies": -1.5, "worm": -3.0,
    "tiny": -1.0, "small": -0.4, "stingy": -1.8, "overpriced": -2.2,
    "expensive": -1.3, "pricey": -1.3,
    # service / place
    "slow": -1.6, "rude": -2.6, "dirty": -2.6, "unclean": -2.5,
    "unhygienic": -3.0, "filthy": -3.0, "noisy": -1.2, "crowded": -0.8,
    "cramped": -1.4, "delayed": -1.5, "delay": -1.4, "late": -0.8,
    "waiting": -0.9, "ignored": -2.0, "unprofessional": -2.2,
    "arrogant": -2.2, "careless": -1.8, "inattentive": -1.8,
    "unfriendly": -2.0, "inefficient": -1.6, "chaotic": -1.6,
    "messy": -1.6, "uncomfortable": -1.6, "stuffy": -1.2,
}

# Multi-word expressions (checked before single words)
PHRASES = {
    "to die for": 3.0,
    "must try": 2.5,
    "worth it": 1.5,
    "value for money": 1.6,
    "money well spent": 1.8,
    "come back": 1.5,
    "go back": 1.2,
    "order again": 1.5,
    "visit again": 1.5,
    "finger licking": 2.5,
    "waste of money": -3.0,
    "waste of time": -2.5,
    "never again": -2.5,
    "food poisoning": -3.0,
    "not worth": -2.0,
    "cold coffee": 0.0,   # a drink, not a complaint
    "cold drink": 0.0,
    "cold drinks": 0.0,
    "cold brew": 0.0,
    "long wait": -1.8,
    "took forever": -2.2,
    "too long": -1.6,
    "no complaints": 1.5,
}

NEGATIONS = {
    "not", "no", "never", "none", "nothing", "neither", "nor", "without",
    "hardly", "barely", "cannot", "cant", "dont", "doesnt", "didnt",
    "wasnt", "werent", "isnt", "arent", "wont", "wouldnt", "couldnt",
    "shouldnt", "hasnt", "havent", "hadnt", "aint", "neednt",
}

INTENSIFIERS = {
    "very": 1.3, "really": 1.3, "extremely": 1.5, "super": 1.4,
    "absolutely": 1.5, "totally": 1.4, "so": 1.25, "too": 1.25,
    "quite": 1.1, "highly": 1.4, "incredibly": 1.5, "truly": 1.3,
    "definitely": 1.3, "particularly": 1.2, "utterly": 1.5,
    "exceptionally": 1.5, "insanely": 1.5, "seriously": 1.3,
}

DAMPENERS = {
    "slightly": 0.7, "somewhat": 0.7, "bit": 0.7, "little": 0.7,
    "kinda": 0.7, "kindof": 0.7, "fairly": 0.85, "mildly": 0.7,
    "barely": 0.6, "marginally": 0.7,
}

# Words after which the *next* clause carries the reviewer's real opinion
CONTRAST_WORDS = {"but", "however", "yet", "except", "unfortunately"}

EMOJI = {
    "😍": 2.5, "❤": 2.0, "👍": 1.8, "😋": 2.2, "🤤": 2.2, "😊": 1.5,
    "😀": 1.5, "😃": 1.5, "🥰": 2.5, "👌": 1.5, "💯": 2.0, "🔥": 1.5,
    "🤮": -3.0, "😡": -2.5, "👎": -2.0, "😠": -2.2, "😞": -1.8,
    "🤢": -3.0, "😤": -1.8, "😒": -1.5, "💩": -2.5,
}

NEGATION_SCOPE = 3          # words after a negation that get flipped
NEGATION_FACTOR = -0.74     # flipped and softened ("not good" != "bad")
NORMALISATION_ALPHA = 15    # compound = x / sqrt(x^2 + alpha)

# thresholds on the -1..1 compound score
POSITIVE_THRESHOLD = 0.25
NEGATIVE_THRESHOLD = -0.25
DISH_POSITIVE_THRESHOLD = 0.2
DISH_NEGATIVE_THRESHOLD = -0.2

# ---------------------------------------------------------------------------
# DISH & ASPECT VOCABULARY
# ---------------------------------------------------------------------------

# canonical dish name -> spellings that map to it
DISH_SYNONYMS: dict[str, list[str]] = {
    "biryani": ["biryani", "biriyani", "briyani", "dum biryani"],
    "dosa": ["dosa", "dosai", "masala dosa", "ghee roast", "rava dosa"],
    "idli": ["idli", "idly", "idlis"],
    "vada": ["vada", "vadai", "medu vada", "wada"],
    "sambar": ["sambar", "sambhar"],
    "chutney": ["chutney"],
    "parotta": ["parotta", "parota", "porotta", "paratha", "parantha"],
    "naan": ["naan", "nan", "butter naan", "garlic naan"],
    "roti": ["roti", "chapati", "chapathi", "phulka", "kulcha"],
    "puri": ["puri", "poori", "bhatura", "bhature"],
    "pongal": ["pongal"],
    "upma": ["upma"],
    "uttapam": ["uttapam", "uthappam"],
    "paneer": ["paneer", "paneer tikka", "paneer butter masala"],
    "butter chicken": ["butter chicken"],
    "chicken": ["chicken", "chicken 65", "chilli chicken"],
    "mutton": ["mutton", "lamb"],
    "fish": ["fish", "fish fry", "fish curry"],
    "prawns": ["prawn", "prawns", "shrimp"],
    "curry": ["curry", "gravy", "masala"],
    "thali": ["thali", "meals", "meal combo"],
    "dal": ["dal", "dhal", "daal"],
    "rasam": ["rasam"],
    "pulao": ["pulao", "pulav", "pilaf"],
    "fried rice": ["fried rice"],
    "noodles": ["noodles", "chowmein", "hakka noodles"],
    "manchurian": ["manchurian", "gobi manchurian"],
    "tikka": ["tikka", "tandoori", "tandoori chicken"],
    "kebab": ["kebab", "kabab", "kebabs", "seekh"],
    "shawarma": ["shawarma", "shawarmas"],
    "samosa": ["samosa", "samosas"],
    "chaat": ["chaat", "pani puri", "bhel", "sev puri"],
    "pav bhaji": ["pav bhaji", "vada pav"],
    "sweet": ["gulab jamun", "jalebi", "halwa", "payasam", "kheer", "laddu",
              "rasmalai", "mysore pak", "sweets"],
    "lassi": ["lassi", "buttermilk"],
    "coffee": ["coffee", "filter coffee", "cappuccino", "latte", "espresso"],
    "tea": ["tea", "chai"],
    "juice": ["juice", "fresh juice"],
    "falooda": ["falooda"],
    "ice cream": ["ice cream", "icecream", "gelato", "sundae"],
    "pizza": ["pizza", "pizzas"],
    "pasta": ["pasta", "spaghetti", "lasagna", "lasagne", "macaroni"],
    "burger": ["burger", "burgers"],
    "sandwich": ["sandwich", "sandwiches", "sub", "panini"],
    "fries": ["fries", "french fries"],
    "salad": ["salad", "salads"],
    "soup": ["soup", "soups"],
    "steak": ["steak", "steaks"],
    "sushi": ["sushi", "sashimi"],
    "ramen": ["ramen"],
    "momos": ["momo", "momos", "dumpling", "dumplings"],
    "wrap": ["wrap", "wraps", "roll", "rolls", "kathi roll"],
    "cake": ["cake", "cakes", "pastry", "pastries", "brownie", "cupcake"],
    "waffle": ["waffle", "waffles", "pancake", "pancakes"],
    "milkshake": ["milkshake", "shake", "smoothie"],
    "tacos": ["taco", "tacos", "nachos", "burrito", "quesadilla"],
    "falafel": ["falafel", "hummus", "pita"],
    "bowl": ["buddha bowl", "poke bowl", "grain bowl"],
    "breakfast": ["breakfast", "brunch"],
    "starter": ["starter", "starters", "appetizer", "appetizers"],
    "dessert": ["dessert", "desserts"],
}

# canonical aspect -> keywords
ASPECT_KEYWORDS: dict[str, list[str]] = {
    "service": ["service", "staff", "waiter", "waiters", "waitress", "server",
                "servers", "manager", "host", "hospitality", "owner"],
    "ambience": ["ambience", "ambiance", "atmosphere", "decor", "interior",
                 "music", "seating", "vibe", "environment"],
    "price": ["price", "prices", "pricing", "cost", "bill", "value", "rates"],
    "cleanliness": ["hygiene", "cleanliness", "washroom", "restroom",
                    "toilet", "toilets"],
    "portion": ["portion", "portions", "quantity"],
    "wait time": ["wait", "waiting", "delivery"],
}

# ---------------------------------------------------------------------------
# TEXT HELPERS
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*|,")
_SENTENCE_SPLIT_RE = re.compile(r"[.!?;\n]+|\s[-–—]\s")


def _clean_token(token: str) -> str:
    """lowercase + remove apostrophes so "wasn't" -> "wasnt"."""
    return token.lower().replace("'", "").replace("’", "")


def _tokenise(text: str) -> list[tuple[str, bool]]:
    """Return (normalised token, is_all_caps) pairs."""
    text = text.replace("’", "'")
    result = []

    for match in _WORD_RE.finditer(text):
        raw = match.group(0)
        is_caps = raw.isupper() and len(raw) > 2
        result.append((_clean_token(raw), is_caps))

    return result


def _build_mention_index() -> tuple[dict[str, tuple[str, str]], int]:
    """Map every spelling (1-3 words) -> (canonical name, 'dish'|'aspect')."""
    index: dict[str, tuple[str, str]] = {}
    longest = 1

    for canonical, spellings in DISH_SYNONYMS.items():
        for spelling in spellings:
            key = " ".join(_clean_token(w) for w in spelling.split())
            index[key] = (canonical, "dish")
            longest = max(longest, len(key.split()))

    for canonical, keywords in ASPECT_KEYWORDS.items():
        for keyword in keywords:
            index.setdefault(keyword, (canonical, "aspect"))

    return index, longest


_MENTION_INDEX, _MAX_MENTION_WORDS = _build_mention_index()


def _singular(token: str) -> str:
    if len(token) > 3 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


# ---------------------------------------------------------------------------
# RESULT TYPES
# ---------------------------------------------------------------------------

@dataclass
class Mention:
    name: str
    kind: str            # "dish" | "aspect"
    score: float         # -1..1 (clause sentiment)
    label: str           # positive | negative | neutral


@dataclass
class ReviewSentiment:
    label: str                       # positive | negative | mixed | neutral
    score: float                     # -1..1 (text only)
    positive_sum: float = 0.0
    negative_sum: float = 0.0
    mentions: list[Mention] = field(default_factory=list)
    word_count: int = 0


@dataclass
class _Clause:
    tokens: list[tuple[str, bool]]
    weight: float = 1.0
    raw: float = 0.0
    pos: float = 0.0
    neg: float = 0.0
    mentions: list[tuple[str, str]] = field(default_factory=list)
    sentence_id: int = 0


# ---------------------------------------------------------------------------
# CORE SCORING
# ---------------------------------------------------------------------------

def compound(raw_sum: float) -> float:
    """Squash an open-ended sum into the range -1..1."""
    if raw_sum == 0:
        return 0.0
    return raw_sum / math.sqrt(raw_sum * raw_sum + NORMALISATION_ALPHA)


def _score_tokens(tokens: list[tuple[str, bool]]) -> tuple[float, float, float]:
    """Return (net, positive_part, negative_part) raw valence for tokens."""
    words = [t for t, _ in tokens]
    net = pos = neg = 0.0
    i = 0

    while i < len(words):
        valence = None
        span = 1

        # ---- phrases (3 words, then 2 words) ----------------------
        for n in (3, 2):
            if i + n <= len(words):
                phrase = " ".join(words[i:i + n])
                if phrase in PHRASES:
                    valence = PHRASES[phrase]
                    span = n
                    break

        # ---- single words -----------------------------------------
        if valence is None:
            word = words[i]
            valence = POSITIVE.get(word)
            if valence is None:
                valence = NEGATIVE.get(word)
            if valence is None:
                # simple plural / -s fallback ("prices", "portions")
                base = _singular(word)
                valence = POSITIVE.get(base) or NEGATIVE.get(base)

        if valence is None or valence == 0:
            i += span
            continue

        # ---- CAPS emphasis ("AMAZING") ----------------------------
        if tokens[i][1]:
            valence *= 1.25

        # ---- intensifiers / dampeners in the 2 preceding words ----
        for back in (1, 2):
            j = i - back
            if j < 0:
                break
            previous = words[j]
            if previous in INTENSIFIERS:
                valence *= INTENSIFIERS[previous]
                break
            if previous in DAMPENERS:
                valence *= DAMPENERS[previous]
                break

        # ---- negation in the preceding NEGATION_SCOPE words -------
        for back in range(1, NEGATION_SCOPE + 1):
            j = i - back
            if j < 0:
                break
            if words[j] in NEGATIONS:
                valence *= NEGATION_FACTOR
                break

        net += valence
        if valence > 0:
            pos += valence
        else:
            neg += -valence

        i += span

    return net, pos, neg


def _find_mentions(
    tokens: list[tuple[str, bool]],
    extra_dishes: dict[str, str],
) -> list[tuple[str, str]]:
    """Find (canonical name, kind) mentions in a token list."""
    words = [t for t, _ in tokens]
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    i = 0

    while i < len(words):
        matched = False

        for n in range(min(_MAX_MENTION_WORDS, len(words) - i), 0, -1):
            gram = " ".join(words[i:i + n])
            candidates = [gram]

            if n == 1:
                candidates.append(_singular(gram))
            else:
                # plural of the last word: "gulab jamuns"
                candidates.append(" ".join(words[i:i + n - 1] + [_singular(words[i + n - 1])]))

            for candidate in candidates:
                hit = extra_dishes.get(candidate) or None
                if hit:
                    entry = (hit, "dish")
                elif candidate in _MENTION_INDEX:
                    entry = _MENTION_INDEX[candidate]
                else:
                    continue

                key = f"{entry[1]}:{entry[0]}"
                if key not in seen:
                    seen.add(key)
                    found.append(entry)

                i += n
                matched = True
                break

            if matched:
                break

        if not matched:
            i += 1

    return found


def _split_clauses(text: str) -> list[_Clause]:
    """Split into clauses; the part after 'but' gets more weight."""
    clauses: list[_Clause] = []

    for sentence_id, sentence in enumerate(_SENTENCE_SPLIT_RE.split(text)):
        tokens = _tokenise(sentence)

        if not tokens:
            continue

        # split at contrast words ("tasty but slow")
        segments: list[list[tuple[str, bool]]] = [[]]
        contrast_positions: list[int] = []

        for token in tokens:
            if token[0] in CONTRAST_WORDS:
                contrast_positions.append(len(segments))
                segments.append([])
            else:
                segments[-1].append(token)

        for index, segment in enumerate(segments):
            if not segment:
                continue

            if contrast_positions:
                # before the contrast word: 0.5, after it: 1.5
                weight = 0.5 if index < contrast_positions[0] else 1.5
            else:
                weight = 1.0

            # commas end a clause too, so negation/intensifiers never leak
            # across them ("not bad, pretty decent")
            piece: list[tuple[str, bool]] = []
            for token in segment + [(",", False)]:
                if token[0] == ",":
                    if piece:
                        clauses.append(
                            _Clause(
                                tokens=piece,
                                weight=weight,
                                sentence_id=sentence_id,
                            )
                        )
                    piece = []
                else:
                    piece.append(token)

    return clauses


def _split_on_and(
    clause: _Clause, extra_dishes: dict[str, str]
) -> list[_Clause]:
    """'biryani was great and dosa was awful' -> two clauses.

    Only splits when both halves mention something AND both carry sentiment,
    so 'the biryani and dosa were great' stays together.
    """
    words = [t for t, _ in clause.tokens]

    if "and" not in words:
        return [clause]

    parts: list[list[tuple[str, bool]]] = [[]]
    for token in clause.tokens:
        if token[0] == "and":
            parts.append([])
        else:
            parts[-1].append(token)

    parts = [p for p in parts if p]

    if len(parts) < 2:
        return [clause]

    scored = []
    for part in parts:
        net, _, _ = _score_tokens(part)
        scored.append((part, net, _find_mentions(part, extra_dishes)))

    # every part must have both a mention and a non-zero sentiment
    if not all(net != 0 and mentions for _, net, mentions in scored):
        return [clause]

    return [
        _Clause(tokens=part, weight=clause.weight, sentence_id=clause.sentence_id)
        for part, _, _ in scored
    ]


_FILLER_WORDS = {"the", "a", "an", "our", "their", "some", "of", "and",
                 "my", "his", "her"}


def _is_pure_mention_list(clause: _Clause, extra_dishes: dict[str, str]) -> bool:
    """True when a clause is only 'the biryani' style list items."""
    words = [t for t, _ in clause.tokens if t not in _FILLER_WORDS]

    if not words:
        return False

    mention_words: set[str] = set()
    for spelling in list(_MENTION_INDEX) + list(extra_dishes):
        mention_words.update(spelling.split())

    return all(w in mention_words or _singular(w) in mention_words for w in words)


def _label_for(score: float, positive_sum: float, negative_sum: float) -> str:
    if positive_sum >= 1.5 and negative_sum >= 1.5 and abs(score) < 0.55:
        return "mixed"
    if score >= POSITIVE_THRESHOLD:
        return "positive"
    if score <= NEGATIVE_THRESHOLD:
        return "negative"
    return "neutral"


def _mention_label(score: float) -> str:
    if score >= DISH_POSITIVE_THRESHOLD:
        return "positive"
    if score <= DISH_NEGATIVE_THRESHOLD:
        return "negative"
    return "neutral"


def analyze_text(
    text: str,
    menu_item_names: list[str] | None = None,
) -> ReviewSentiment:
    """Analyse one review.

    `menu_item_names` lets the analyser recognise dishes that are specific to
    this restaurant's own menu (in addition to the built-in dish vocabulary).
    """
    text = (text or "").strip()

    extra_dishes: dict[str, str] = {}
    for name in menu_item_names or []:
        key = " ".join(_clean_token(w) for w in name.split())
        if key:
            extra_dishes[key] = name.strip().lower()
            extra_dishes[_singular(key)] = name.strip().lower()

    # ---- emoji contribution ----------------------------------------
    emoji_net = sum(v for ch, v in EMOJI.items() if ch in text)

    # ---- clause scoring --------------------------------------------
    base_clauses = _split_clauses(text)
    clauses: list[_Clause] = []

    for clause in base_clauses:
        clauses.extend(_split_on_and(clause, extra_dishes))

    total = emoji_net
    pos_sum = max(emoji_net, 0.0)
    neg_sum = max(-emoji_net, 0.0)
    word_count = 0

    for clause in clauses:
        net, pos, neg = _score_tokens(clause.tokens)
        clause.raw, clause.pos, clause.neg = net, pos, neg
        clause.mentions = _find_mentions(clause.tokens, extra_dishes)

        total += net * clause.weight
        pos_sum += pos
        neg_sum += neg
        word_count += len(clause.tokens)

    # exclamation marks add mild emphasis in the direction of the opinion
    exclamations = min(text.count("!"), 3)
    if total > 0:
        total += exclamations * 0.3
    elif total < 0:
        total -= exclamations * 0.3

    score = compound(total)
    label = _label_for(score, pos_sum, neg_sum)

    # ---- dish / aspect mentions ------------------------------------
    per_mention: dict[tuple[str, str], list[float]] = {}

    for index, clause in enumerate(clauses):
        if not clause.mentions:
            continue

        clause_score = compound(clause.raw)

        if clause_score == 0 and index + 1 < len(clauses):
            following = clauses[index + 1]

            # "We ordered biryani and dosa. Both were amazing."
            # -> a neutral mention inherits from the next mention-less clause.
            if not following.mentions and following.raw != 0:
                clause_score = compound(following.raw)

            # "The biryani, dosa and chutney were excellent"
            # -> "The biryani" is just a list item; it shares the opinion
            #    expressed by the clause that follows it.
            elif (
                following.sentence_id == clause.sentence_id
                and following.raw != 0
                and _is_pure_mention_list(clause, extra_dishes)
            ):
                clause_score = compound(following.raw)

        for name, kind in clause.mentions:
            per_mention.setdefault((name, kind), []).append(clause_score)

    mentions = []
    for (name, kind), scores in per_mention.items():
        average = sum(scores) / len(scores)
        mentions.append(
            Mention(
                name=name,
                kind=kind,
                score=round(average, 3),
                label=_mention_label(average),
            )
        )

    return ReviewSentiment(
        label=label,
        score=round(score, 3),
        positive_sum=round(pos_sum, 3),
        negative_sum=round(neg_sum, 3),
        mentions=mentions,
        word_count=word_count,
    )


def blend_with_rating(text_score: float, rating: int | None) -> float:
    """Combine text sentiment with the star rating (70% text / 30% stars)."""
    if rating is None:
        return text_score

    rating_signal = (rating - 3) / 2          # 1★ -> -1 ... 5★ -> +1
    return round(0.7 * text_score + 0.3 * rating_signal, 3)


def label_for_score(score: float, positive_sum: float, negative_sum: float) -> str:
    """Public wrapper used after blending text with the rating."""
    return _label_for(score, positive_sum, negative_sum)
