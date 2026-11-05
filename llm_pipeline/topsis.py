"""
topsis.py — Standalone TOPSIS module for foil ranking
Bachelor Thesis: Contrastive Explanations in the era of LLMs

Ports the Java TOPSIS logic from ContrastiveExplanationService.java.

Usage:
    from topsis import run_topsis

    winner, scores = run_topsis(
        candidates=tc["candidate_rules"],
        weights={"Precondition_Similarity": 0.25, "Ownership": 0.20,
                 "Frequency": 0.10, "Occurrence": 0.45},
        cc_type="CC1"
    )
    print(winner["rule_name"], scores)

The winner is the candidate with the highest P_i (proximity to ideal solution).
"""

import math


# ── Criteria mapping ───────────────────────────────────────────────────────────
# Maps JSON attribute keys → weight dict keys
ATTR_MAP = {
    "precondition_similarity": "Precondition_Similarity",
    "ownership": "Ownership",
    "frequency": "Frequency",
    "occurrence": "Occurrence",
}

# Criteria used per CC type
CRITERIA_CC1_CC2 = ["precondition_similarity", "ownership", "frequency", "occurrence"]
CRITERIA_CC3     = ["ownership", "frequency", "occurrence"]   # no precondition_similarity


def run_topsis(candidates: list[dict], weights: dict, cc_type: str) -> tuple[dict, dict]:
    """
    Run TOPSIS on the candidate rules and return the best candidate and scores.

    Parameters
    ----------
    candidates : list of dicts, each with "rule_name" and "attributes" dict.
                 Attributes: precondition_similarity (float|None), ownership (int),
                             frequency (int), occurrence (int).
    weights    : dict with keys Precondition_Similarity, Ownership, Frequency, Occurrence.
                 Must sum to 1.0 (normalized internally as a safety net).
    cc_type    : "CC1", "CC2", or "CC3". Determines which criteria are used.
                 CC2 also uses 4 criteria (same as CC1); CC3 omits Precondition_Similarity.

    Returns
    -------
    winner     : the candidate dict with the highest P_i
    scores     : dict mapping rule_name → P_i score (float, higher = better)
    """
    if not candidates:
        raise ValueError("No candidates provided.")

    # Select criteria based on CC type
    criteria = CRITERIA_CC3 if cc_type == "CC3" else CRITERIA_CC1_CC2

    # Build weight vector (normalized internally)
    raw_weights = {c: weights.get(ATTR_MAP[c], 0.0) for c in criteria}
    total_weight = sum(raw_weights.values())
    if total_weight <= 0:
        raise ValueError("All weights are zero — cannot run TOPSIS.")
    norm_weights = {c: raw_weights[c] / total_weight for c in criteria}

    # Build raw score matrix: [[score_c1, score_c2, ...], ...]
    n = len(candidates)
    m = len(criteria)
    matrix = []
    for cand in candidates:
        row = []
        attrs = cand.get("attributes", {})
        for c in criteria:
            val = attrs.get(c)
            row.append(float(val) if val is not None else 0.0)
        matrix.append(row)

    # Step 1: Vector normalisation (divide by column's Euclidean norm)
    col_norms = []
    for j in range(m):
        col_sq_sum = sum(matrix[i][j] ** 2 for i in range(n))
        col_norms.append(math.sqrt(col_sq_sum) if col_sq_sum > 0 else 0.0)

    norm_matrix = []
    for i in range(n):
        row = []
        for j in range(m):
            denom = col_norms[j]
            row.append(matrix[i][j] / denom if denom > 0 else 0.0)
        norm_matrix.append(row)

    # Step 2: Weighted normalised matrix
    weighted = []
    for i in range(n):
        row = [norm_matrix[i][j] * norm_weights[criteria[j]] for j in range(m)]
        weighted.append(row)

    # Step 3: Ideal best (A+) and ideal worst (A-)  — higher is better for all criteria
    a_plus  = [max(weighted[i][j] for i in range(n)) for j in range(m)]
    a_minus = [min(weighted[i][j] for i in range(n)) for j in range(m)]

    # Step 4: Distances to ideal best and worst
    s_plus  = []
    s_minus = []
    for i in range(n):
        dp = math.sqrt(sum((weighted[i][j] - a_plus[j])  ** 2 for j in range(m)))
        dm = math.sqrt(sum((weighted[i][j] - a_minus[j]) ** 2 for j in range(m)))
        s_plus.append(dp)
        s_minus.append(dm)

    # Step 5: Relative closeness P_i = s_minus / (s_plus + s_minus)
    p_scores = []
    for i in range(n):
        denom = s_plus[i] + s_minus[i]
        p_scores.append(s_minus[i] / denom if denom > 0 else 0.0)

    # Best = highest P_i
    best_idx  = p_scores.index(max(p_scores))
    scores    = {candidates[i]["rule_name"]: round(p_scores[i], 6) for i in range(n)}
    winner    = candidates[best_idx]

    return winner, scores
