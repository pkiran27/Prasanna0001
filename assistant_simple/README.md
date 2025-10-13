# Quotes Assistant (Rasa Open Source)

Short restatement: Build a runnable Rasa Open Source conversational agent (local) with at least one original custom action and submit code for evaluation by 19th Oct EOD; allow the team to demo it online.

This repository contains a small, fully runnable Rasa 3.x assistant that:
- Shares quotes from a local JSON file
- Lets users add their own quotes (persisted locally)
- Remembers the last quote via a slot
- Optionally fetches an online quote from a public API with robust offline fallback

## What to inspect
- `domain.yml`: intents, slots, responses, action names
- `data/`: `nlu.yml`, `stories.yml`, `rules.yml`
- `actions/actions.py`: original custom actions using `rasa-sdk`
- `config.yml`: DIETClassifier + TEDPolicy
- `endpoints.yml`: action endpoint at `http://localhost:5055/webhook`

## Environment setup (Rasa Open Source only)
Follow legacy Rasa OSS local instructions. This project targets Python 3.8–3.11 and Rasa 3.6.

1. Create venv and install deps:
```bash
cd assistant_simple
./setup.sh
source .venv/bin/activate
```

2. Train the model:
```bash
rasa train
```

3. In one terminal, run the action server:
```bash
rasa run actions --port 5055 --cors "*"
```

4. In another terminal, run the assistant shell:
```bash
rasa shell --debug
```

Alternatively, run the helper script (spawns actions in background, then opens shell):
```bash
./train_and_run.sh
```

## Demo phrases (2-minute script)
Type the following in `rasa shell`:
- `hi`
- `give me a quote`
- `add quote: "Be curious. Not judgmental."`
- `show last quote`
- `fetch an online quote` (works online; if blocked, falls back to local)
- `bye`

## Custom actions overview
- `action_get_local_quote`: Reads from local `quotes_db.json` and sets `last_quote`.
- `action_add_quote`: Extracts quoted text from your message, persists it to `quotes_db.json`, and sets `last_quote`.
- `action_show_last_quote`: Reads `last_quote` slot and replies with it.
- `action_fetch_quote_api`: Calls a public API (`https://zenquotes.io/api/random`) with timeout and try/except. On failure, falls back to a local quote. Always sets `last_quote`.

Security/offline note: No secrets or API keys used. If the environment has no network, the assistant will gracefully fall back to local quotes.

## Submission checklist (what to submit)
- Zipped project folder with all source files
- Include `README.md` and `HOW_TO_RUN.txt`
- Include scripts: `setup.sh`, `train_and_run.sh`, `scaffold.py`
- Ensure `quotes_db.json` is present
- Verifier can run: train, start actions, open shell, type demo phrases

## Troubleshooting
- If `rasa` is not found, ensure the venv is active: `source .venv/bin/activate`
- If training fails on Python version, use Python 3.8–3.11
- To see more internals, run with `--debug`
