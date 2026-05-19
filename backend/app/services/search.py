import re
import json
from typing import List, Optional, Tuple
from ..models import Product

# ============================================================
# SYNONYMS & ALIASES
# ============================================================

SYNONYM_MAP = {
    "hanky": "handkerchief",
    "hankie": "handkerchief",
    "mafuta": "petroleum jelly",
    "tissue": "serviette",
    "serviette": "tissue",
    "soda": "mineral water",
    "soap": "bar soap",
    "milk": "fresh milk",
    "bread": "bread",
    "sugar": "sugar",
    "rice": "rice",
    "cooking oil": "cooking oil",
    "oil": "cooking oil",
    "flour": "wheat flour",
    "unga": "maize flour",
    "sukari": "sugar",
    "mchele": "rice",
    "mkate": "bread",
    "maziwa": "milk",
    "sabuni": "soap",
    "dawa ya meno": "toothpaste",
    "batteries": "batteries",
    "diapers": "diapers",
    "pasta": "pasta",
    "sardines": "sardines",
    "matches": "matches",
    "margarine": "margarine",
    "washing powder": "washing powder",
    "tea": "tea leaves",
}

# ============================================================
# TOKEN PROCESSING
# ============================================================

def _tokenize(text: str) -> List[str]:
    """Split text into lowercase tokens, stripping punctuation."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _expand_query(query: str) -> set:
    """Expand a query with synonyms."""
    tokens = _tokenize(query)
    expanded = set(tokens)
    for tok in tokens:
        if tok in SYNONYM_MAP:
            expanded.add(SYNONYM_MAP[tok])
            # Also tokenize the synonym
            expanded.update(_tokenize(SYNONYM_MAP[tok]))
    return expanded


def _get_search_tokens(product) -> set:
    """Get all searchable tokens for a product (name + aliases + tags + keywords)."""
    tokens = set(_tokenize(product.name or ""))
    tokens.add((product.name or "").lower())

    # Aliases
    if product.aliases:
        try:
            alias_list = json.loads(product.aliases) if isinstance(product.aliases, str) else product.aliases
            for alias in alias_list:
                tokens.add(alias.lower())
                tokens.update(_tokenize(alias))
        except (json.JSONDecodeError, TypeError):
            tokens.update(_tokenize(str(product.aliases)))

    # Tags
    if product.tags:
        try:
            tag_list = json.loads(product.tags) if isinstance(product.tags, str) else product.tags
            for tag in tag_list:
                tokens.update(_tokenize(tag))
        except (json.JSONDecodeError, TypeError):
            tokens.update(_tokenize(str(product.tags)))

    # Search keywords
    if product.search_keywords:
        tokens.update(_tokenize(product.search_keywords))

    # Category
    if product.category:
        tokens.update(_tokenize(product.category))

    # Supplier
    if product.supplier:
        tokens.update(_tokenize(product.supplier))

    return tokens


# ============================================================
# WEIGHTED SCORING ENGINE
# ============================================================

# Score thresholds
EXACT_MATCH_SCORE = 100
ALIAS_MATCH_SCORE = 95
STARTS_WITH_SCORE = 85
CONTAINS_SCORE = 70
TOKEN_OVERALL_SCORE = 60
TOKEN_PARTIAL_SCORE = 45
FUZZY_HIGH_SCORE = 50
FUZZY_LOW_SCORE = 25
SEMANTIC_BOOST = 10

# Ambiguity threshold: if multiple products score above this, ask clarification
AMBIGUITY_THRESHOLD = 50


def score_product(query: str, product) -> Tuple[float, str]:
    """
    Score a single product against a query using weighted criteria.
    Returns (score, reason) where score is 0-100.
    """
    query_lower = query.lower().strip()
    query_tokens = _tokenize(query_lower)
    query_expanded = _expand_query(query)

    name_lower = (product.name or "").lower()
    search_tokens = _get_search_tokens(product)

    # 1. Exact name match (highest priority)
    if query_lower == name_lower:
        return EXACT_MATCH_SCORE, "exact_name"

    if query_lower in search_tokens:
        return ALIAS_MATCH_SCORE, "alias_match"

    # 2. Starts with
    if name_lower.startswith(query_lower):
        return STARTS_WITH_SCORE, "starts_with"

    # 3. Contains (whole query as substring of name)
    if query_lower in name_lower:
        return CONTAINS_SCORE, "contains"

    # 4. Check aliases for substring match
    if product.aliases:
        try:
            alias_list = json.loads(product.aliases) if isinstance(product.aliases, str) else product.aliases
            for alias in alias_list:
                alias_lower = alias.lower()
                if query_lower == alias_lower:
                    return ALIAS_MATCH_SCORE, "alias_exact"
                if query_lower in alias_lower:
                    return CONTAINS_SCORE - 5, "alias_contains"
        except (json.JSONDecodeError, TypeError):
            pass

    # 5. Token overlap scoring
    if query_tokens:
        name_words = _tokenize(name_lower)
        # Also get tokens from search_tokens (excluding the full name)
        all_name_tokens = set(name_words) | {t for t in search_tokens if len(t) > 1}

        # Count matching tokens
        matched = sum(1 for qt in query_tokens if qt in all_name_tokens)
        if matched > 0:
            ratio = matched / len(query_tokens)
            if ratio >= 0.8:
                return TOKEN_OVERALL_SCORE + 15, f"token_high_{matched}/{len(query_tokens)}"
            elif ratio >= 0.5:
                return TOKEN_OVERALL_SCORE + 5, f"token_medium_{matched}/{len(query_tokens)}"
            else:
                return TOKEN_OVERALL_SCORE - 10, f"token_low_{matched}/{len(query_tokens)}"

        # 6. Partial token match (substring within words)
        partial = 0
        for qt in query_tokens:
            for nt in all_name_tokens:
                if len(qt) > 2 and len(nt) > 2 and (qt in nt or nt in qt):
                    partial += 1
                    break
        if partial > 0:
            score = TOKEN_PARTIAL_SCORE + (partial / len(query_tokens)) * 15
            return score, f"partial_{partial}/{len(query_tokens)}"

    # 7. Fallback: check expanded query tokens against search tokens
    query_set = set(query_tokens)
    search_intersection = query_set & search_tokens
    if search_intersection:
        ratio = len(search_intersection) / len(query_set) if query_set else 0
        return max(FUZZY_LOW_SCORE, min(FUZZY_HIGH_SCORE, 30 + ratio * 30)), "semantic_fallback"

    return 0, "no_match"


def rank_products(query: str, products: List) -> List[Tuple]:
    """
    Rank all products by relevance to query.
    Returns list of (product, score, reason) sorted by score descending.
    """
    scored = []
    for p in products:
        score, reason = score_product(query, p)
        if score > 0:
            scored.append((p, score, reason))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def detect_ambiguity(scored: List[Tuple], threshold: float = AMBIGUITY_THRESHOLD) -> Tuple[bool, List]:
    """
    Detect if multiple products exceed the confidence threshold.
    Returns (is_ambiguous, candidate_list).
    """
    top_candidates = [(p, s, r) for p, s, r in scored if s >= threshold]

    if len(top_candidates) == 0:
        # No strong match, return top 3 weak matches
        return False, scored[:3]

    if len(top_candidates) == 1:
        # One clear winner
        return False, top_candidates

    # Check if the top candidate is significantly better than the rest
    top_score = top_candidates[0][1]
    second_score = top_candidates[1][1]

    # If top is more than 20 points ahead, no ambiguity
    if len(top_candidates) >= 2 and (top_score - second_score) > 20:
        return False, top_candidates[:1]

    # Multiple candidates within close range → ambiguous
    return True, top_candidates


def build_clarification_response(candidates: List[Tuple]) -> dict:
    """Build a clarification response from candidate products."""
    matches = []
    for i, (p, score, reason) in enumerate(candidates, 1):
        matches.append({
            "id": p.id,
            "name": p.name,
            "category": p.category or "",
            "supplier": p.supplier or "",
            "score": round(score, 1),
        })

    match_list = "\n".join(f"{i}. **{m['name']}**" + (f" ({m['category']})" if m['category'] else "") for i, m in enumerate(matches, 1))

    response = (
        f"I found multiple matching products:\n\n"
        f"{match_list}\n\n"
        f"Which one did you mean?"
    )

    return {
        "type": "clarification_required",
        "matches": matches,
        "response": response,
    }


def build_no_match_response(query: str) -> str:
    """Build a response when no products match."""
    return (
        f"I couldn't find any product matching '{query}'.\n\n"
        f"Please check the product name or add it in the Products section."
    )
