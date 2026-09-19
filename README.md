# Jev authorship check

A throwaway experiment using [Jev](https://typesafe.ai/) to classify a piece of text as primarily human-written, AI-generated, or uncertain.

This is not an AI detector you should trust as evidence. It is just a quick way to see whether Jev gives a useful signal for a particular set of examples.

## Run it

Set your TypeSafe key in the shell. The key is never stored by this project.

```bash
export TYPESAFE_API_KEY='your-key'
python3 jev_check.py sample.txt
```

Or pipe text into it:

```bash
printf 'Some text to check.' | python3 jev_check.py
```

The output includes the selected label, confidence and the full probability distribution.

## Labels

- `human`
- `ai_generated`
- `uncertain`

The script deliberately includes `uncertain` for short, edited or ambiguous text. A classification is only a model judgement, not proof of authorship.

## Tests

The tests do not call Jev or need an API key:

```bash
python3 -m unittest discover -s tests -v
```
