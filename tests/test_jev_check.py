import io
import json
import os
import sys
import unittest
from unittest.mock import mock_open, patch

import jev_check


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps(
            {
                "model": "jev-latest",
                "answers": {
                    "authorship": {
                        "type": "choice",
                        "choice": "uncertain",
                        "probabilities": {
                            "human": 0.2,
                            "ai_generated": 0.3,
                            "uncertain": 0.5,
                        },
                        "confidence": 0.5,
                    }
                },
            }
        ).encode()


class JevCheckTests(unittest.TestCase):
    def test_diagnose_result_identifies_low_specificity(self):
        result = {
            "label": "uncertain",
            "signals": {
                "personal_specificity": {"type": "score", "score": 0.0},
                "concrete_evidence": {"type": "noul", "noul": 0.2},
                "formulaic_style": {"type": "noul", "noul": 0.3},
            },
        }
        diagnosis = jev_check.diagnose_result(result)
        self.assertEqual(diagnosis["category"], "needs-concrete-evidence")
        self.assertIn("observe", diagnosis["question"].lower())

    def test_diagnose_result_identifies_human_led_ai_assistance(self):
        result = {
            "label": "human",
            "signals": {
                "human_authored": {"type": "noul", "noul": 0.85},
                "ai_assistance": {"type": "noul", "noul": 0.75},
                "fully_ai_generated": {"type": "noul", "noul": 0.2},
                "personal_specificity": {"type": "score", "score": 1.6},
                "concrete_evidence": {"type": "noul", "noul": 0.8},
                "formulaic_style": {"type": "noul", "noul": 0.2},
            },
        }
        self.assertEqual(
            jev_check.diagnose_result(result)["category"],
            "human-led-but-ai-assisted",
        )

    def test_render_review_report_includes_text_and_editorial_question(self):
        results = [{
            "file": "article.md",
            "section": "Introduction",
            "paragraph_index": 7,
            "word_count": 12,
            "text": "This shows the importance of choosing the right tool.",
            "label": "uncertain",
            "confidence": 0.38,
            "probabilities": {"human": 0.27, "ai_generated": 0.14, "uncertain": 0.59},
            "signals": {
                "personal_specificity": {"score": 0.0},
                "concrete_evidence": {"noul": 0.1},
                "formulaic_style": {"noul": 0.4},
            },
        }]
        report = jev_check.render_review_report(results)
        self.assertIn("Paragraph 7", report)
        self.assertIn("This shows the importance", report)
        self.assertIn("needs-concrete-evidence", report)
        self.assertIn("What did you actually observe", report)

    @patch("jev_check.urllib.request.urlopen", return_value=FakeResponse())
    def test_request_sends_typed_authorship_question(self, urlopen):
        jev_check.request_jev("hello", "test-key")
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "jev-latest")
        self.assertEqual(payload["questions"]["authorship"]["type"], "choice")
        self.assertIn("uncertain", payload["questions"]["authorship"]["criteria"])
        self.assertEqual(payload["questions"]["human_authored"]["type"], "noul")
        self.assertEqual(payload["questions"]["ai_assistance"]["type"], "noul")
        self.assertEqual(payload["questions"]["fully_ai_generated"]["type"], "noul")
        self.assertEqual(payload["questions"]["personal_specificity"]["type"], "score")
        self.assertEqual(payload["questions"]["formulaic_style"]["type"], "noul")
        self.assertEqual(payload["questions"]["concrete_evidence"]["type"], "noul")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")

    def test_markdown_chunks_keep_frontmatter_in_full_mode(self):
        text = "---\ntitle: Test\n---\n\n# First\n\nOne paragraph.\n\nTwo paragraphs.\n\n## Second\n\nAnother paragraph."
        chunks = jev_check.markdown_chunks(text, "paragraph", True)
        self.assertEqual(len(chunks), 3)
        self.assertIn("title: Test", chunks[0]["text"])
        self.assertEqual(chunks[0]["section"], "First")
        self.assertEqual(chunks[2]["section"], "Second")

    def test_markdown_chunks_can_make_sections(self):
        text = "# First\n\nOne.\n\n## Second\n\nTwo."
        chunks = jev_check.markdown_chunks(text, "section", False)
        self.assertEqual([chunk["section"] for chunk in chunks], ["First", "Second"])

    def test_body_mode_removes_frontmatter_only_when_requested(self):
        with patch("builtins.open", mock_open(read_data="---\ntitle: Test\n---\n\nBody")):
            self.assertIn("title: Test", jev_check.read_text("article.md", "full"))
            self.assertEqual(jev_check.read_text("article.md", "body"), "Body")

    def test_read_text_from_stdin(self):
        with patch.object(sys, "stdin", io.StringIO("hello from stdin")):
            self.assertEqual(jev_check.read_text(None), "hello from stdin")


if __name__ == "__main__":
    unittest.main()
