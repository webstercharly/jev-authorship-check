# Jev authorship check

A small experiment using [Jev](https://typesafe.ai/) to classify Markdown as human-written, AI-assisted, AI-generated, or uncertain.

It also asks for structured signals in the same request:

- human authorship
- meaningful AI assistance
- fully AI-generated text
- personal specificity
- formulaic or templated style
- concrete evidence such as events, measurements or tools

This is not an AI detector you should trust as evidence. It is a quick way to see whether Jev gives a useful signal for a particular set of examples.

## Run one file

Set your TypeSafe key in the shell. The key is never stored by this project.

```bash
export TYPESAFE_API_KEY='your-key'
python3 jev_check.py article.md
```

By default, Markdown is sent exactly as supplied, including Astro frontmatter.

To classify only the article body while leaving the source file untouched:

```bash
python3 jev_check.py article.md --state body
```

Or pipe text into it:

```bash
printf 'Some text to check.' | python3 jev_check.py
```

## Run a batch

Pass several files directly:

```bash
python3 jev_check.py article-one.md article-two.md
```

Or use a recursive glob:

```bash
python3 jev_check.py --glob 'personal-site/src/content/blog/_drafts/*.md'
```

Batch mode prints one JSON object per line, which makes the output easy to save or process with another script. Each result includes the authorship label, probabilities, confidence and all structured signals.

## Tests

The tests do not call Jev or need an API key:

```bash
python3 -m unittest discover -s tests -v
```
