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

    def test_body_mode_removes_frontmatter_only_when_requested(self):
        with patch("builtins.open", mock_open(read_data="---\ntitle: Test\n---\n\nBody")):
            self.assertIn("title: Test", jev_check.read_text("article.md", "full"))
            self.assertEqual(jev_check.read_text("article.md", "body"), "Body")

    def test_read_text_from_stdin(self):
        with patch.object(sys, "stdin", io.StringIO("hello from stdin")):
            self.assertEqual(jev_check.read_text(None), "hello from stdin")


if __name__ == "__main__":
    unittest.main()
