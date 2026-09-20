import unittest

import jev_blog_review


class BlogReviewTests(unittest.TestCase):
    def test_questions_include_authorship_and_editorial_signals(self):
        self.assertIn("authorship", jev_blog_review.QUESTIONS)
        for name in (
            "observed_event",
            "author_action",
            "evidence_boundary",
            "generic_language",
            "ending_type",
            "paragraph_removability",
        ):
            self.assertIn(name, jev_blog_review.QUESTIONS)

    def test_editorial_question_targets_generic_ending(self):
        result = {
            "signals": {
                "generic_language": {"noul": 0.2},
                "observed_event": {"noul": 0.8},
                "author_action": {"noul": 0.8},
                "evidence_boundary": {"noul": 0.8},
                "ending_type": {"choice": "general_lesson"},
                "paragraph_removability": {"noul": 0.8},
            }
        }
        self.assertIn("concrete consequence", jev_blog_review.editorial_question(result))

    def test_render_report_keeps_blog_text_and_signals_together(self):
        result = {
            "file": "/tmp/article.md",
            "section": "Introduction",
            "paragraph_index": 1,
            "text": "I checked the output and changed the workflow.",
            "label": "human",
            "confidence": 0.8,
            "signals": {
                "personal_specificity": {"score": 1.5},
                "concrete_evidence": {"noul": 0.8},
                "observed_event": {"noul": 0.9},
                "author_action": {"noul": 0.9},
                "evidence_boundary": {"noul": 0.4},
                "generic_language": {"noul": 0.1},
                "ending_type": {"choice": "decision"},
                "paragraph_removability": {"noul": 0.9},
            },
        }
        report = jev_blog_review.render_report([result])
        self.assertIn("I checked the output", report)
        self.assertIn("Observed event: `0.9`", report)
        self.assertIn("Ending type: `decision`", report)


if __name__ == "__main__":
    unittest.main()
