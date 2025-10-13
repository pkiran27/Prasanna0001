#!/usr/bin/env python3
"""
Regenerate core files for the minimal quotes assistant.
This script is optional; it writes baseline files if missing.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FILES = {
    "config.yml": """# Rasa 3.x configuration
language: en
pipeline:
  - name: WhitespaceTokenizer
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: CountVectorsFeaturizer
    analyzer: char_wb
    min_ngram: 3
    max_ngram: 5
  - name: DIETClassifier
    epochs: 100
  - name: EntitySynonymMapper
  - name: ResponseSelector
    epochs: 100
policies:
  - name: MemoizationPolicy
  - name: RulePolicy
  - name: TEDPolicy
    epochs: 100
""",
    "domain.yml": """version: \"3.1\"\n\nintents:\n  - greet\n  - goodbye\n  - ask_quote\n  - add_quote\n  - show_last_quote\n  - fetch_quote_api\n  - ask_help\n\nslots:\n  last_quote:\n    type: text\n    influence_conversation: false\n    mappings:\n      - type: custom\n\nresponses:\n  utter_greet:\n    - text: \"Hi! I can share quotes, remember the last one, and even save yours. Try: 'give me a quote', 'add quote: \"Your text\"', or 'show last quote'.\"\n  utter_goodbye:\n    - text: \"Goodbye! Talk soon.\"\n  utter_help:\n    - text: \"I understand: greet, goodbye, ask for a quote, fetch an online quote, add a quote you provide, and show the last quote I told you.\"\n  utter_ack_add:\n    - text: \"Saved your quote. You can say 'show last quote' to hear it again.\"\n\nactions:\n  - action_get_local_quote\n  - action_add_quote\n  - action_show_last_quote\n  - action_fetch_quote_api\n\nsession_config:\n  session_expiration_time: 60\n  carry_over_slots_to_new_session: true\n""",
    "endpoints.yml": """action_endpoint:\n  url: \"http://localhost:5055/webhook\"\n""",
    "credentials.yml": """rest:\n""",
}

DATA_FILES = {
    ROOT / "data" / "nlu.yml": """version: \"3.1\"\n\nnlu:\n- intent: greet\n  examples: |\n    - hi\n    - hello\n- intent: goodbye\n  examples: |\n    - bye\n- intent: ask_quote\n  examples: |\n    - give me a quote\n""",
    ROOT / "data" / "stories.yml": """version: \"3.1\"\n\nstories:\n- story: local\n  steps:\n    - intent: ask_quote\n    - action: action_get_local_quote\n""",
    ROOT / "data" / "rules.yml": """version: \"3.1\"\n\nrules:\n- rule: greet\n  steps:\n    - intent: greet\n    - action: utter_greet\n""",
}

ACTIONS_INIT = ROOT / "actions" / "__init__.py"
ACTIONS_FILE = ROOT / "actions" / "actions.py"
DB_FILE = ROOT / "quotes_db.json"


def main() -> None:
    (ROOT / "actions").mkdir(parents=True, exist_ok=True)
    (ROOT / "data").mkdir(parents=True, exist_ok=True)

    for name, content in FILES.items():
        path = ROOT / name
        if not path.exists():
            path.write_text(content)

    for path, content in DATA_FILES.items():
        if not path.exists():
            path.write_text(content)

    if not ACTIONS_INIT.exists():
        ACTIONS_INIT.write_text("# actions package\n")

    if not ACTIONS_FILE.exists():
        ACTIONS_FILE.write_text(
            "from rasa_sdk import Action\n\nclass ActionPing(Action):\n    def name(self): return 'action_ping'\n    def run(self, dispatcher, tracker, domain): dispatcher.utter_message(text='pong'); return []\n"
        )

    if not DB_FILE.exists():
        DB_FILE.write_text(json.dumps([
            {"text": "Simplicity is the ultimate sophistication.", "author": "Leonardo da Vinci"}
        ], indent=2))

    print("Scaffold ensured.")


if __name__ == "__main__":
    main()
