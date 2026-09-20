# Jev authorship check

A small experiment using [Jev](https://typesafe.ai/) to inspect Markdown as human-written, AI-assisted, AI-generated, or uncertain.

It asks for structured signals in the same request:

- human authorship
- meaningful AI assistance
- fully AI-generated text
- personal specificity
- formulaic or templated style
- concrete evidence such as events, measurements or tools

It can judge a whole file or split it into Markdown sections or paragraphs so that differences in writing style can be located.

This is not an AI detector you should trust as evidence. It is a quick way to see whether Jev gives a useful signal for a particular set of examples.

## Run one file

Set your TypeSafe key in the shell. The key is never stored by this project.

```bash
export TYPESAFE_API_KEY='your-key'
python3 jev_check.py article.md
```

By default, the complete Markdown is sent, including Astro frontmatter.

To classify only the article body while leaving the source file untouched:

```bash
python3 jev_check.py article.md --state body
```

## Inspect sections or paragraphs

Judge each Markdown section:

```bash
python3 jev_check.py article.md --granularity section --state body
```

Judge each paragraph:

```bash
python3 jev_check.py article.md --granularity paragraph --state body
```

Chunked output is one JSON object per line and includes the section name, paragraph index, chunk position and word count. Add `--include-text` when you want the chunk text in the output.

## Generate an editorial review report

Use the structured Jev signals to identify paragraphs that need more truthful
specificity or concrete evidence:

```bash
python3 jev_check.py article.md \
  --granularity paragraph \
  --state body \
  --review-report review.md
```

The report includes the paragraph text, raw signal values, a local editorial
diagnosis and a question to guide revision. It does not rewrite text or try to
optimise for detector behaviour. The source file is unchanged.

## Review blog writing

Use the separate blog-specific script when the purpose is editorial improvement:

```bash
python3 jev_blog_review.py \
  --glob '/path/to/blog/_drafts/*.md' \
  --state body \
  --review-report blog-review.md
```

This adds typed questions about observed events, author actions, evidence
boundaries, generic language, paragraph endings and whether each paragraph has
a concrete reason to remain. It keeps the text beside the raw signals and
does not edit source files.

To pull out only the paragraphs worth rewriting yourself:

```bash
python3 jev_blog_review.py \
  --glob '/path/to/blog/_drafts/*.md' \
  --state body \
  --review-report blog-review.md \
  --shortlist-report human-rewrite-shortlist.md
```

The shortlist selects paragraphs where Jev is uncertain or reports a high
generic-language signal. It does not use an AI-authorship label as a reason to
rewrite. The full paragraph is included with an editorial question so short
sentences are judged in context.

## Run a batch

Pass several files directly:

```bash
python3 jev_check.py article-one.md article-two.md --granularity paragraph
```

Or use a recursive glob:

```bash
python3 jev_check.py --glob 'personal-site/src/content/blog/_drafts/*.md' --granularity paragraph --state body
```

The output can be saved as JSONL for later review:

```bash
python3 jev_check.py --glob '*.md' --granularity paragraph --state body > results.jsonl
```

## Tests

The tests do not call Jev or need an API key:

```bash
python3 -m unittest discover -s tests -v
```
