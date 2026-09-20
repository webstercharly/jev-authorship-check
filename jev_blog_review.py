#!/usr/bin/env python3
"""Jev editorial review for blog prose.

This is deliberately separate from the general authorship classifier. It asks
editorial questions about grounded writing and never rewrites source text.
"""

import argparse
import glob
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import jev_check

BLOG_QUESTIONS = {
    "observed_event": {
        "type": "noul",
        "instructions": "Does this paragraph describe something the author actually observed happening, rather than only a general idea?",
    },
    "author_action": {
        "type": "noul",
        "instructions": "Does this paragraph make clear what the author did, checked, decided or changed?",
    },
    "evidence_boundary": {
        "type": "noul",
        "instructions": "Does this paragraph state a meaningful limit on what the evidence proves or covers?",
    },
    "generic_language": {
        "type": "noul",
        "instructions": "Does this paragraph rely mainly on portable, generic wording that could fit many unrelated articles?",
    },
    "ending_type": {
        "type": "choice",
        "instructions": "What does the paragraph mainly end on?",
        "criteria": {
            "consequence": "A concrete result or changed behaviour",
            "decision": "A decision or next action",
            "observation": "A specific observation or measured finding",
            "general_lesson": "A broad lesson or maxim",
            "generic_summary": "A summary that adds little beyond the preceding text",
            "uncertain": "The ending type cannot be determined",
        },
    },
    "paragraph_removability": {
        "type": "noul",
        "instructions": "Would removing this paragraph lose a concrete event, decision, measurement or necessary boundary from the article?",
    },
}

QUESTIONS = {**jev_check.QUESTIONS, **BLOG_QUESTIONS}


def request_blog_jev(text: str, api_key: str) -> dict:
    payload = {"model": "jev-latest", "state": text, "questions": QUESTIONS}
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        jev_check.API_URL,
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in (429, 529) or attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("Jev request failed after retries")


def simplify(result: dict) -> dict:
    answers = result["answers"]
    authorship = answers["authorship"]
    return {
        "label": authorship.get("choice"),
        "confidence": authorship.get("confidence"),
        "probabilities": authorship.get("probabilities"),
        "signals": {key: answers.get(key) for key in QUESTIONS if key != "authorship"},
        "model": result.get("model"),
    }


def signal(result: dict, name: str, field: str = "noul"):
    value = result.get("signals", {}).get(name, {}).get(field)
    return value if isinstance(value, (int, float)) else "n/a"


def editorial_question(result: dict) -> str:
    if signal(result, "generic_language") != "n/a" and signal(result, "generic_language") >= 0.7:
        return "Which sentence is doing real work, and which wording is just a portable template?"
    if signal(result, "observed_event") != "n/a" and signal(result, "observed_event") < 0.45:
        return "What did you actually observe happening here?"
    if signal(result, "author_action") != "n/a" and signal(result, "author_action") < 0.45:
        return "What did you personally do, check, decide or change?"
    if signal(result, "evidence_boundary") != "n/a" and signal(result, "evidence_boundary") < 0.45:
        return "What does this evidence not prove or cover?"
    if result.get("signals", {}).get("ending_type", {}).get("choice") in {"general_lesson", "generic_summary"}:
        return "Can the paragraph end on a concrete consequence, decision or observation instead?"
    if signal(result, "paragraph_removability") != "n/a" and signal(result, "paragraph_removability") < 0.45:
        return "What would the article lose if this paragraph were removed?"
    return "Does this paragraph preserve your actual judgement and experience?"


def shortlist_reasons(result: dict, generic_threshold: float = 0.7) -> list[str]:
    """Return reasons a paragraph merits a human rewrite pass.

    Authorship is deliberately not a reason here. Jev's authorship label is
    editorial triage at best, not evidence that a paragraph needs rewriting.
    """
    reasons = []
    if result.get("label") == "uncertain":
        reasons.append("Jev was uncertain about the paragraph")
    generic = signal(result, "generic_language")
    if generic != "n/a" and generic >= generic_threshold:
        reasons.append(f"generic-language signal {generic:.2f}")
    return reasons


def render_shortlist_report(results: list[dict], generic_threshold: float = 0.7) -> str:
    """Render only paragraphs that should receive a human rewrite pass."""
    selected = [result for result in results if shortlist_reasons(result, generic_threshold)]
    lines = [
        "# Jev human rewrite shortlist",
        "",
        "These paragraphs were selected for a human rewrite pass. This is editorial triage, not an authorship or AI-detection result.",
        "",
    ]
    if not selected:
        lines.extend(["No paragraphs met the shortlist criteria.", ""])
        return "\n".join(lines)
    for number, result in enumerate(selected, 1):
        reasons = "; ".join(shortlist_reasons(result, generic_threshold))
        ending = result.get("signals", {}).get("ending_type", {}).get("choice", "n/a")
        lines.extend([
            f"## {number}. {Path(result.get('file', 'stdin')).name} — {result.get('section', 'Introduction')} — paragraph {result.get('paragraph_index', number)}",
            "",
            f"- Why it was selected: {reasons}",
            f"- Jev label: `{result.get('label', 'n/a')}`",
            f"- Personal specificity: `{signal(result, 'personal_specificity', 'score')}`",
            f"- Concrete evidence: `{signal(result, 'concrete_evidence')}`",
            f"- Generic language: `{signal(result, 'generic_language')}`",
            f"- Ending type: `{ending}`",
            "",
            "> **Rewrite this paragraph yourself**",
            "> " + result.get("text", "[text not included]").replace("\n", "\n> "),
            "",
            f"**Question to answer:** {editorial_question(result)}",
            "",
        ])
    return "\n".join(lines)


def render_report(results: list[dict]) -> str:
    lines = [
        "# Jev blog writing review",
        "",
        "Editorial feedback for truthful, specific writing. Not a detector-evasion scorecard.",
        "",
    ]
    for number, result in enumerate(results, 1):
        paragraph = result.get("paragraph_index") or number
        ending = result.get("signals", {}).get("ending_type", {}).get("choice", "n/a")
        lines.extend([
            f"## {Path(result.get('file', 'stdin')).name} — {result.get('section', 'Introduction')} — paragraph {paragraph}",
            "",
            f"- Jev label: `{result.get('label', 'n/a')}`",
            f"- Label confidence: `{result.get('confidence', 'n/a')}`",
            f"- Personal specificity: `{signal(result, 'personal_specificity', 'score')}`",
            f"- Concrete evidence: `{signal(result, 'concrete_evidence')}`",
            f"- Observed event: `{signal(result, 'observed_event')}`",
            f"- Author action: `{signal(result, 'author_action')}`",
            f"- Evidence boundary: `{signal(result, 'evidence_boundary')}`",
            f"- Generic language: `{signal(result, 'generic_language')}`",
            f"- Ending type: `{ending}`",
            f"- Paragraph removability: `{signal(result, 'paragraph_removability')}`",
            "",
            "> **Text**",
            "> " + result.get("text", "[text not included]").replace("\n", "\n> "),
            "",
            f"**Editorial question:** {editorial_question(result)}",
            "",
        ])
    return "\n".join(lines)


def expand_paths(paths: list[str], patterns: list[str]) -> list[str]:
    found = list(paths)
    for pattern in patterns:
        found.extend(glob.glob(pattern, recursive=True))
    unique = sorted({str(Path(path)) for path in found})
    if not unique:
        raise ValueError("No input files matched")
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description="Review blog prose with Jev's grounded-writing questions")
    parser.add_argument("files", nargs="*", help="Markdown files to review")
    parser.add_argument("--glob", action="append", default=[], help="glob pattern; may be repeated")
    parser.add_argument("--state", choices=("full", "body"), default="body")
    parser.add_argument("--review-report", required=True, help="write the Markdown review report")
    parser.add_argument("--shortlist-report", help="write only paragraphs selected for human rewriting")
    parser.add_argument("--generic-threshold", type=float, default=0.7, help="generic-language threshold for the shortlist (default: 0.7)")
    args = parser.parse_args()
    try:
        api_key = os.environ.get("TYPESAFE_API_KEY")
        if not api_key:
            raise ValueError("Set TYPESAFE_API_KEY before making a Jev request")
        paths = expand_paths(args.files, args.glob)
        results = []
        for path in paths:
            with open(path, encoding="utf-8") as file:
                original = file.read()
            text = jev_check.body_only(original) if args.state == "body" else original
            chunks = jev_check.markdown_chunks(text, "paragraph", False)
            for index, chunk in enumerate(chunks, 1):
                result = simplify(request_blog_jev(chunk["text"], api_key))
                result.update({
                    "file": path,
                    "state": args.state,
                    "granularity": "paragraph",
                    "section": chunk["section"],
                    "paragraph_index": chunk["paragraph_index"] or index,
                    "chunk_index": index,
                    "chunk_count": len(chunks),
                    "word_count": len(chunk["text"].split()),
                    "text": chunk["text"],
                })
                results.append(result)
        for result in results:
            print(json.dumps(result))
        with open(args.review_report, "w", encoding="utf-8") as report_file:
            report_file.write(render_report(results))
        if args.shortlist_report:
            with open(args.shortlist_report, "w", encoding="utf-8") as shortlist_file:
                shortlist_file.write(render_shortlist_report(results, args.generic_threshold))
    except (OSError, ValueError, urllib.error.HTTPError, urllib.error.URLError) as error:
        print(f"error: {error}", file=__import__("sys").stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
