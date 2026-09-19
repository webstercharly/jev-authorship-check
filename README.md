# Jev authorship check

A small experiment using [Jev](https://typesafe.ai/) to classify Markdown as primarily human-written, AI-generated, or uncertain.

It also asks for three structured signals in the same request:

- personal specificity
- formulaic or templated style
- concrete evidence such as events, measurements or tools

This is not an AI detector you should trust as evidence. It is a quick way to see whether Jev gives a useful signal for a particular set of examples. Markdown is sent as supplied, including Astro frontmatter.

## Run one file

Set your TypeSafe key in the shell. The key is never stored by this project.

```bash
export TYPESAFE_API_KEY='your-key'
python3 jev_check.py article.md
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

Batch mode prints one JSON object per line, which makes the output easy to save or process with another script.

Each result includes the authorship label, probabilities, confidence and the three structured signals.

## Tests

The tests do not call Jev or need an API key:

```bash
python3 -m unittest discover -s tests -v
```
