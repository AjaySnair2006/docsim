"""
=====================================================================
ADAPTER FOR: AI Semantic Similarity module (Teammate #2)
=====================================================================

INTEGRATION CONTRACT
---------------------
Teammate #2 must provide a function with (roughly) this signature:

    def compute_similarity(doc_a: dict, doc_b: dict) -> dict:
        \"\"\"
        doc_a / doc_b are shaped like:
            {"filename": str, "total_pages": int,
             "pages": [{"page_number": int, "text": str}, ...]}

        Returns:
        {
            "overall_similarity": 82.5,   # 0-100
            "page_pair_scores": [
                {"doc_a_page": 1, "doc_b_page": 1, "similarity_score": 91.2},
                {"doc_a_page": 1, "doc_b_page": 2, "similarity_score": 40.0},
                ...
            ]
        }
        \"\"\"

HOW TO CONNECT THE REAL MODULE
-------------------------------
1. Drop teammate #2's package into `backend/app/external/similarity/`.
2. Replace the import inside `_call_real_similarity_module()` below with
   the real one, e.g.:
       from app.external.similarity.engine import compute_similarity
3. Any API keys the model needs (OpenAI, HuggingFace, etc.) should be read
   from `app.config.settings` (which pulls from environment variables) —
   never hardcode them here.
=====================================================================
"""

from app.config import settings
from collections import Counter
from math import log
import re


class SimilarityComputationError(Exception):
    def __init__(self, message: str, code: str = "SIMILARITY_COMPUTATION_FAILED"):
        self.message = message
        self.code = code
        super().__init__(message)


def _call_real_similarity_module(doc_a: dict, doc_b: dict) -> dict:
    from app.external.similarity.engine import compute_similarity  # type: ignore

    return compute_similarity(doc_a, doc_b, api_key=settings.AI_MODULE_API_KEY)


def _stub_similarity_module(doc_a: dict, doc_b: dict) -> dict:
    """
    Compare normalized word shingles so formatting and punctuation changes do
    not dominate the result. The global score penalizes unmatched content in
    either document, and page assignments are one-to-one.
    """
    pages_a = doc_a["pages"]
    pages_b = doc_b["pages"]
    tokens_a = [_token_shingles(page["text"]) for page in pages_a]
    tokens_b = [_token_shingles(page["text"]) for page in pages_b]

    page_frequency = Counter(
        shingle
        for page_shingles in tokens_a + tokens_b
        for shingle in page_shingles
    )
    page_count = len(tokens_a) + len(tokens_b)
    idf = {
        shingle: log((page_count + 1) / (frequency + 1)) + 1
        for shingle, frequency in page_frequency.items()
    }
    vectors_a = [_weighted_shingles(shingles, idf) for shingles in tokens_a]
    vectors_b = [_weighted_shingles(shingles, idf) for shingles in tokens_b]

    pair_details = []
    assignment_weights = []
    for vector_a in vectors_a:
        row = []
        details_row = []
        for vector_b in vectors_b:
            score, overlap = _weighted_dice(vector_a, vector_b)
            row.append(overlap)
            details_row.append(score)
        assignment_weights.append(row)
        pair_details.append(details_row)

    assignments = _maximum_weight_assignment(assignment_weights)
    page_pair_scores = []
    matched_overlap = 0.0
    for index_a, page_a in enumerate(pages_a):
        index_b = assignments[index_a] if index_a < len(assignments) else None
        overlap = 0.0
        score = 0.0
        page_b_number = None
        if index_b is not None and index_b < len(pages_b):
            overlap = assignment_weights[index_a][index_b]
            if overlap > 0:
                score = pair_details[index_a][index_b]
                page_b_number = pages_b[index_b]["page_number"]
                matched_overlap += overlap
        page_pair_scores.append(
            {
                "doc_a_page": page_a["page_number"],
                "doc_b_page": page_b_number,
                "similarity_score": round(score, 2),
            }
        )

    total_weight_a = sum(sum(vector.values()) for vector in vectors_a)
    total_weight_b = sum(sum(vector.values()) for vector in vectors_b)
    total_weight = total_weight_a + total_weight_b
    overall = 2 * matched_overlap / total_weight * 100 if total_weight else 0.0
    return {
        "overall_similarity": round(overall, 2),
        "page_pair_scores": page_pair_scores,
    }


def _token_shingles(text: str) -> Counter:
    shingles = Counter()
    sentences = re.split(r"(?<=[.!?])\s+|[\r\n]+", text.casefold())
    for sentence in sentences:
        tokens = re.findall(r"\w+", sentence)
        if not tokens:
            continue
        shingle_size = min(3, len(tokens))
        shingles.update(
            tuple(tokens[index : index + shingle_size])
            for index in range(len(tokens) - shingle_size + 1)
        )
    return shingles


def _weighted_shingles(shingles: Counter, idf: dict) -> dict:
    return {
        shingle: count * idf[shingle]
        for shingle, count in shingles.items()
    }


def _weighted_dice(vector_a: dict, vector_b: dict) -> tuple[float, float]:
    weight_a = sum(vector_a.values())
    weight_b = sum(vector_b.values())
    if not weight_a or not weight_b:
        return 0.0, 0.0
    overlap = sum(
        min(weight, vector_b.get(shingle, 0.0))
        for shingle, weight in vector_a.items()
    )
    score = 2 * overlap / (weight_a + weight_b) * 100
    return score, overlap


def _maximum_weight_assignment(weights: list[list[float]]) -> list[int | None]:
    """Return the maximum-overlap one-to-one page assignment (Hungarian method)."""
    row_count = len(weights)
    column_count = max((len(row) for row in weights), default=0)
    size = max(row_count, column_count)
    if not size:
        return []

    max_weight = max((weight for row in weights for weight in row), default=0.0)
    costs = [
        [
            max_weight - weights[row][column]
            if row < row_count and column < len(weights[row])
            else max_weight
            for column in range(size)
        ]
        for row in range(size)
    ]

    row_potential = [0.0] * (size + 1)
    column_potential = [0.0] * (size + 1)
    column_row = [0] * (size + 1)
    previous_column = [0] * (size + 1)
    for row in range(1, size + 1):
        column_row[0] = row
        current_column = 0
        minimum_cost = [float("inf")] * (size + 1)
        used = [False] * (size + 1)
        while True:
            used[current_column] = True
            current_row = column_row[current_column]
            delta = float("inf")
            next_column = 0
            for column in range(1, size + 1):
                if used[column]:
                    continue
                reduced_cost = (
                    costs[current_row - 1][column - 1]
                    - row_potential[current_row]
                    - column_potential[column]
                )
                if reduced_cost < minimum_cost[column]:
                    minimum_cost[column] = reduced_cost
                    previous_column[column] = current_column
                if minimum_cost[column] < delta:
                    delta = minimum_cost[column]
                    next_column = column
            for column in range(size + 1):
                if used[column]:
                    row_potential[column_row[column]] += delta
                    column_potential[column] -= delta
                else:
                    minimum_cost[column] -= delta
            current_column = next_column
            if column_row[current_column] == 0:
                break
        while True:
            next_column = previous_column[current_column]
            column_row[current_column] = column_row[next_column]
            current_column = next_column
            if current_column == 0:
                break

    assignment: list[int | None] = [None] * row_count
    for column in range(1, size + 1):
        row = column_row[column] - 1
        assigned_column = column - 1
        if row < row_count and assigned_column < column_count:
            assignment[row] = assigned_column
    return assignment


def compute(doc_a: dict, doc_b: dict) -> dict:
    """
    Public function used by the /compare route.
    doc_a / doc_b should be dicts (use `.model_dump()` on an ExtractedDocument).
    """
    try:
        try:
            return _call_real_similarity_module(doc_a, doc_b)
        except ModuleNotFoundError:
            return _stub_similarity_module(doc_a, doc_b)
    except SimilarityComputationError:
        raise
    except Exception as exc:
        raise SimilarityComputationError(f"Similarity computation failed: {exc}")
