import unittest

from app.services.similarity_module_adapter import (
    _maximum_weight_assignment,
    _stub_similarity_module,
)
from app.services.report_module_adapter import _stub_analysis_module


def make_document(name, page_texts):
    return {
        "filename": name,
        "total_pages": len(page_texts),
        "pages": [
            {"page_number": index, "text": text}
            for index, text in enumerate(page_texts, start=1)
        ],
    }


class SimilarityFallbackTests(unittest.TestCase):
    def compare(self, texts_a, texts_b):
        return _stub_similarity_module(
            make_document("a.pdf", texts_a), make_document("b.pdf", texts_b)
        )

    def test_normalizes_case_and_punctuation(self):
        result = self.compare(
            ["The quick brown fox jumps over the lazy dog."],
            ["THE QUICK BROWN FOX jumps, over the lazy dog!"],
        )

        self.assertEqual(result["overall_similarity"], 100.0)

    def test_sentence_reordering_preserves_overlap(self):
        result = self.compare(
            ["alpha beta gamma delta epsilon. one two three four five."],
            ["one two three four five. alpha beta gamma delta epsilon."],
        )

        self.assertGreaterEqual(result["overall_similarity"], 95.0)

    def test_unmatched_pages_reduce_overall_similarity(self):
        result = self.compare(
            ["shared research methods and detailed analysis"],
            [
                "shared research methods and detailed analysis",
                *["unrelated content about economics and finance"] * 9,
            ],
        )

        self.assertLess(result["overall_similarity"], 40.0)

    def test_pages_are_matched_one_to_one(self):
        result = self.compare(
            [
                "a copied page with enough words to compare",
                "a copied page with enough words to compare",
            ],
            ["a copied page with enough words to compare"],
        )
        matched_pages = [
            pair["doc_b_page"]
            for pair in result["page_pair_scores"]
            if pair["doc_b_page"] is not None
        ]

        self.assertEqual(len(matched_pages), 1)

    def test_assignment_finds_global_maximum(self):
        self.assertEqual(_maximum_weight_assignment([[9, 8], [8, 0]]), [1, 0])

    def test_reports_copied_sentence_inside_unrelated_page_text(self):
        passage = (
            "The original researchers carefully documented a distinctive "
            "sequence of experimental procedures before publishing their final results."
        )
        document_a = make_document("a.pdf", [passage])
        document_b = make_document(
            "b.pdf",
            [
                "An unrelated opening about a different subject. "
                + passage
                + " Additional unrelated discussion follows afterward."
            ],
        )
        similarity = _stub_similarity_module(document_a, document_b)
        analysis = _stub_analysis_module(document_a, document_b, similarity)

        self.assertLess(similarity["overall_similarity"], 75.0)
        self.assertTrue(
            any("distinctive sequence" in section["doc_a_excerpt"]
                for section in analysis["similar_sections"])
        )


if __name__ == "__main__":
    unittest.main()