import unittest

import numpy as np

from app.services.content_similarity_adapter import compare_content


class FakeEmbeddingModel:
    def encode(self, texts, **kwargs):
        vectors = []
        for text in texts:
            words = set(text.casefold().split())
            if words & {"car", "automobile", "vehicle", "passengers", "people"}:
                vectors.append([1.0, 0.0])
            else:
                vectors.append([0.0, 1.0])
        return np.asarray(vectors)


def make_document(name, texts):
    return {
        "filename": name,
        "total_pages": len(texts),
        "pages": [
            {"page_number": index, "text": text}
            for index, text in enumerate(texts, start=1)
        ],
    }


class ContentSimilarityTests(unittest.TestCase):
    def test_semantic_paraphrase_is_returned_as_content_match(self):
        document_a = make_document("a.pdf", ["A car carries people across roads."])
        document_b = make_document(
            "b.pdf", ["An automobile transports passengers along streets."]
        )

        result = compare_content(document_a, document_b, FakeEmbeddingModel())

        self.assertEqual(result["content_similarity"], 100.0)
        self.assertEqual(len(result["content_similar_sections"]), 1)
        self.assertEqual(
            result["content_similar_sections"][0]["doc_b_excerpt"],
            "An automobile transports passengers along streets.",
        )

    def test_unrelated_pages_do_not_become_semantic_matches(self):
        document_a = make_document("a.pdf", ["A car carries people across roads."])
        document_b = make_document("b.pdf", ["Quantum particles behave differently."])

        result = compare_content(document_a, document_b, FakeEmbeddingModel())

        self.assertEqual(result["content_similarity"], 0.0)
        self.assertEqual(result["content_similar_sections"], [])
        self.assertIsNone(
            result["content_page_wise_stats"][0]["matched_page_in_other_doc"]
        )

    def test_content_score_penalizes_unmatched_document_pages(self):
        document_a = make_document("a.pdf", ["A car carries people across roads."])
        document_b = make_document(
            "b.pdf",
            [
                "An automobile transports passengers along streets.",
                "Quantum particles behave differently in experiments.",
            ],
        )

        result = compare_content(document_a, document_b, FakeEmbeddingModel())

        self.assertLess(result["content_similarity"], 70.0)
        self.assertEqual(len(result["content_similar_sections"]), 1)


if __name__ == "__main__":
    unittest.main()