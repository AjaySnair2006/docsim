import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pypdf import PdfReader

from app.services.report_module_adapter import _stub_report_module


class ReportTests(unittest.TestCase):
    def test_report_includes_both_matched_excerpts(self):
        comparison = {
            "document_a_name": "a.pdf",
            "document_b_name": "b.pdf",
            "overall_similarity": 72.0,
            "content_similarity": 84.0,
            "similar_sections": [
                {
                    "doc_a_page": 1,
                    "doc_b_page": 2,
                    "similarity_score": 91.0,
                    "doc_a_excerpt": "Distinctive source wording appears in this passage.",
                    "doc_b_excerpt": "The matching passage is shown in the other source.",
                }
            ],
            "content_similar_sections": [
                {
                    "doc_a_page": 1,
                    "doc_b_page": 2,
                    "similarity_score": 84.0,
                    "doc_a_excerpt": "A first semantic example passage.",
                    "doc_b_excerpt": "A second semantic example passage.",
                }
            ],
        }

        with TemporaryDirectory() as directory:
            output_path = _stub_report_module(
                comparison, str(Path(directory) / "report.pdf")
            )
            report_text = "\n".join(
                page.extract_text() for page in PdfReader(output_path).pages
            )

        for excerpt in (
            "Distinctive source wording",
            "matching passage is shown",
            "A first semantic example passage",
            "A second semantic example passage",
        ):
            with self.subTest(excerpt=excerpt):
                self.assertIn(excerpt, report_text)


if __name__ == "__main__":
    unittest.main()