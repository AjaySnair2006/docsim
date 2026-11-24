"""Semantic page comparison backed by a cached sentence-transformer model."""

import os
import re
from threading import Lock

import numpy as np

from app.config import settings
from app.models import PageStat, SimilarSection
from app.services.similarity_module_adapter import _maximum_weight_assignment


class ContentSimilarityError(Exception):
    def __init__(self, message: str, code: str = "CONTENT_SIMILARITY_FAILED"):
        self.message = message
        self.code = code
        super().__init__(message)


_model = None
_model_lock = Lock()
_MAX_CHUNK_WORDS = 100


def _load_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                try:
                    os.environ.setdefault("USE_TF", "0")
                    from sentence_transformers import SentenceTransformer
                except ModuleNotFoundError as exc:
                    raise ContentSimilarityError(
                        "Semantic content comparison requires sentence-transformers. "
                        "Install the backend requirements and retry."
                    ) from exc
                try:
                    _model = SentenceTransformer(settings.CONTENT_SIMILARITY_MODEL)
                except Exception as exc:
                    raise ContentSimilarityError(
                        f"Could not load semantic model '{settings.CONTENT_SIMILARITY_MODEL}': {exc}"
                    ) from exc
    return _model


def _text_chunks(text: str) -> list[tuple[str, int]]:
    sentences = re.split(r"(?<=[.!?])\s+|[\r\n]+", text)
    chunks = []
    current_words = []
    for sentence in sentences:
        words = sentence.split()
        while words:
            available = _MAX_CHUNK_WORDS - len(current_words)
            current_words.extend(words[:available])
            words = words[available:]
            if len(current_words) == _MAX_CHUNK_WORDS:
                chunks.append((" ".join(current_words), len(current_words)))
                current_words = []
    if current_words:
        chunks.append((" ".join(current_words), len(current_words)))
    return chunks


def _encode_page_vectors(
    documents: list[dict], model
) -> tuple[list[np.ndarray], list[list[int]]]:
    page_texts = [document["pages"] for document in documents]
    page_counts = [len(pages) for pages in page_texts]
    chunk_texts = []
    chunk_locations = []
    for document_index, pages in enumerate(page_texts):
        for page_index, page in enumerate(pages):
            for text, word_count in _text_chunks(page["text"]):
                chunk_texts.append(text)
                chunk_locations.append((document_index, page_index, word_count))

    if not chunk_texts:
        return [np.zeros((count, 0), dtype=float) for count in page_counts], [
            [0] * count for count in page_counts
        ]

    chunk_vectors = np.asarray(
        model.encode(
            chunk_texts,
            batch_size=32,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ),
        dtype=float,
    )
    page_vectors = [
        np.zeros((count, chunk_vectors.shape[1]), dtype=float)
        for count in page_counts
    ]
    page_word_counts = [[0] * count for count in page_counts]
    for vector, (document_index, page_index, word_count) in zip(
        chunk_vectors, chunk_locations
    ):
        page_vectors[document_index][page_index] += vector * word_count
        page_word_counts[document_index][page_index] += word_count

    for document_index, vectors in enumerate(page_vectors):
        for page_index, word_count in enumerate(page_word_counts[document_index]):
            if word_count:
                vector = vectors[page_index] / word_count
                norm = np.linalg.norm(vector)
                if norm:
                    vectors[page_index] = vector / norm
    return page_vectors, page_word_counts


def compare_content(doc_a: dict, doc_b: dict, model=None) -> dict:
    """Return a separate meaning-based score and one-to-one semantic page matches."""
    try:
        if model is None:
            if not any(
                page["text"].strip()
                for document in (doc_a, doc_b)
                for page in document["pages"]
            ):
                page_vectors, page_word_counts = _encode_page_vectors(
                    [doc_a, doc_b], _EmptyEncoder()
                )
            else:
                page_vectors, page_word_counts = _encode_page_vectors(
                    [doc_a, doc_b], _load_model()
                )
        else:
            page_vectors, page_word_counts = _encode_page_vectors(
                [doc_a, doc_b], model
            )

        vectors_a, vectors_b = page_vectors
        word_counts_a, word_counts_b = page_word_counts
        if vectors_a.shape[1] and vectors_b.shape[1]:
            cosine_scores = np.clip(vectors_a @ vectors_b.T, -1.0, 1.0)
        else:
            cosine_scores = np.zeros((len(vectors_a), len(vectors_b)))

        threshold = settings.CONTENT_SIMILARITY_THRESHOLD
        assignment_weights = [
            [
                max(0.0, float(cosine_scores[index_a, index_b]) - threshold)
                * min(word_counts_a[index_a], word_counts_b[index_b])
                for index_b in range(len(vectors_b))
            ]
            for index_a in range(len(vectors_a))
        ]
        assignments = _maximum_weight_assignment(assignment_weights)

        page_stats = []
        similar_sections = []
        matched_content = 0.0
        for index_a, page_a in enumerate(doc_a["pages"]):
            index_b = assignments[index_a] if index_a < len(assignments) else None
            matched_page = None
            score = 0.0
            if index_b is not None and index_b < len(doc_b["pages"]):
                cosine = float(cosine_scores[index_a, index_b])
                if cosine >= threshold and word_counts_a[index_a] and word_counts_b[index_b]:
                    score = max(0.0, cosine) * 100
                    matched_page = doc_b["pages"][index_b]["page_number"]
                    matched_content += cosine * min(
                        word_counts_a[index_a], word_counts_b[index_b]
                    )
                    similar_sections.append(
                        SimilarSection(
                            doc_a_page=page_a["page_number"],
                            doc_b_page=matched_page,
                            doc_a_excerpt=page_a["text"][:200],
                            doc_b_excerpt=doc_b["pages"][index_b]["text"][:200],
                            similarity_score=round(score, 2),
                        ).model_dump()
                    )
            page_stats.append(
                PageStat(
                    page_number=page_a["page_number"],
                    matched_page_in_other_doc=matched_page,
                    similarity_score=round(score, 2),
                ).model_dump()
            )

        total_content = sum(word_counts_a) + sum(word_counts_b)
        overall = 2 * matched_content / total_content * 100 if total_content else 0.0
        return {
            "content_similarity": round(overall, 2),
            "content_similar_sections": similar_sections,
            "content_page_wise_stats": page_stats,
        }
    except ContentSimilarityError:
        raise
    except Exception as exc:
        raise ContentSimilarityError(f"Semantic content comparison failed: {exc}") from exc


class _EmptyEncoder:
    def encode(self, *args, **kwargs):
        return np.empty((0, 0))


def compute(doc_a: dict, doc_b: dict) -> dict:
    return compare_content(doc_a, doc_b)