"""Hybrid retrieval helpers for metadata-constrained lexical + semantic search."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import math
import re

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_ITERABLE_FILTER_TYPES = (list, tuple, set, frozenset)


@dataclass(frozen=True)
class HybridRetrievalQuery:
    """Query parameters for hybrid lexical/semantic retrieval."""

    query_text: str
    query_embedding: Sequence[float] | None = None
    metadata_filters: Mapping[str, object] = field(default_factory=dict)
    top_k: int = 20
    lexical_weight: float = 0.35
    semantic_weight: float = 0.65
    min_combined_score: float = 0.0

    def __post_init__(self) -> None:
        if self.top_k <= 0:
            raise ValueError("top_k must be > 0")
        if self.lexical_weight < 0 or self.semantic_weight < 0:
            raise ValueError("lexical_weight and semantic_weight must be >= 0")
        if self.query_embedding is not None and len(self.query_embedding) == 0:
            raise ValueError("query_embedding cannot be empty")
        if self.query_embedding is not None and (self.lexical_weight + self.semantic_weight) <= 0:
            raise ValueError("semantic retrieval requires lexical_weight + semantic_weight > 0")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


def _lexical_score(query_text: str, chunk_text: str) -> float:
    query_tokens = _tokenize(query_text)
    if not query_tokens:
        return 0.0

    chunk_token_set = set(_tokenize(chunk_text))
    if not chunk_token_set:
        return 0.0

    matches = sum(1 for token in query_tokens if token in chunk_token_set)
    return matches / len(query_tokens)


def _cosine_similarity(lhs: Sequence[float], rhs: Sequence[float]) -> float:
    if len(lhs) != len(rhs):
        return 0.0

    dot = sum(left * right for left, right in zip(lhs, rhs, strict=False))
    lhs_norm = math.sqrt(sum(value * value for value in lhs))
    rhs_norm = math.sqrt(sum(value * value for value in rhs))
    if lhs_norm == 0.0 or rhs_norm == 0.0:
        return 0.0
    return dot / (lhs_norm * rhs_norm)


def _semantic_score(query_embedding: Sequence[float], candidate_embedding: object) -> float:
    if not isinstance(candidate_embedding, Sequence):
        return 0.0
    if len(candidate_embedding) == 0:
        return 0.0

    try:
        candidate_vector = [float(value) for value in candidate_embedding]
    except (TypeError, ValueError):
        return 0.0

    return _cosine_similarity([float(value) for value in query_embedding], candidate_vector)


def _minmax_normalize(scores: list[float]) -> list[float]:
    if not scores:
        return []

    minimum = min(scores)
    maximum = max(scores)
    if math.isclose(minimum, maximum):
        if math.isclose(maximum, 0.0):
            return [0.0 for _ in scores]
        return [1.0 for _ in scores]

    denominator = maximum - minimum
    return [(score - minimum) / denominator for score in scores]


def _matches_filters(record: Mapping[str, object], filters: Mapping[str, object]) -> bool:
    for key, expected in filters.items():
        actual = record.get(key)
        if isinstance(expected, _ITERABLE_FILTER_TYPES):
            if actual not in expected:
                return False
            continue
        if actual != expected:
            return False
    return True


def hybrid_retrieve(
    records: Iterable[Mapping[str, object]],
    query: HybridRetrievalQuery,
) -> list[dict[str, object]]:
    """
    Retrieve top candidates combining metadata filtering, lexical, and vector signals.

    Returns candidate rows with `lexical_score`, `semantic_score`, and `combined_score`
    while preserving source/provenance identifiers from the input records.
    """
    filtered = [record for record in records if _matches_filters(record, query.metadata_filters)]
    if not filtered:
        return []

    lexical_scores = [
        _lexical_score(query.query_text, str(record.get("chunk_text", "")))
        for record in filtered
    ]
    lexical_normalized = _minmax_normalize(lexical_scores)

    semantic_enabled = query.query_embedding is not None
    semantic_scores = (
        [
            _semantic_score(query.query_embedding, record.get("embedding"))
            for record in filtered
        ]
        if semantic_enabled
        else [0.0 for _ in filtered]
    )
    semantic_normalized = _minmax_normalize(semantic_scores)

    if semantic_enabled:
        weight_total = query.lexical_weight + query.semantic_weight
        lexical_weight = query.lexical_weight / weight_total
        semantic_weight = query.semantic_weight / weight_total
    else:
        lexical_weight = 1.0
        semantic_weight = 0.0

    scored_rows: list[dict[str, object]] = []
    for index, record in enumerate(filtered):
        combined_score = (
            lexical_normalized[index] * lexical_weight
            + semantic_normalized[index] * semantic_weight
        )
        if combined_score < query.min_combined_score:
            continue

        row = dict(record)
        row["lexical_score"] = lexical_normalized[index]
        row["semantic_score"] = semantic_normalized[index]
        row["combined_score"] = combined_score
        scored_rows.append(row)

    scored_rows.sort(
        key=lambda row: (
            -float(row["combined_score"]),
            -float(row["semantic_score"]),
            -float(row["lexical_score"]),
            str(row.get("document_chunk_id", "")),
        )
    )
    return scored_rows[: query.top_k]
