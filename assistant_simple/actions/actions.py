import json
import os
from typing import Any, Dict, List, Text

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "quotes_db.json")


def _load_quotes() -> List[Dict[str, str]]:
    """Load quotes from the local JSON file. If missing or invalid, return a safe default list.

    The JSON structure is a list of objects: [{"text": ..., "author": ...}, ...]
    """
    if not os.path.exists(DB_PATH):
        return [
            {"text": "Simplicity is the soul of efficiency.", "author": "Austin Freeman"},
            {"text": "Well begun is half done.", "author": "Aristotle"},
        ]
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [q for q in data if isinstance(q, dict) and "text" in q]
        return []
    except Exception:
        # Corrupt file or invalid JSON; prefer to recover
        return [
            {"text": "Act only according to that maxim whereby you can at the same time will that it should become a universal law.", "author": "Immanuel Kant"}
        ]


def _save_quotes(quotes: List[Dict[str, str]]) -> None:
    """Persist quotes to the local JSON file atomically where possible."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    tmp_path = DB_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, DB_PATH)


class ActionGetLocalQuote(Action):
    """Return a quote from the local JSON store and set the last_quote slot.

    This action does not perform network access and is safe offline.
    """

    def name(self) -> Text:
        return "action_get_local_quote"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        quotes = _load_quotes()
        # Choose a quote deterministically using conversation turn to keep demos consistent
        index = (len(tracker.events) or 0) % len(quotes)
        quote = quotes[index]
        text = quote.get("text", "Here's a quote.")
        author = quote.get("author", "Unknown")
        message = f"\"{text}\" — {author}"
        dispatcher.utter_message(text=message)
        return [SlotSet("last_quote", message)]


class ActionAddQuote(Action):
    """Add a user-provided quote into the local JSON file and set last_quote.

    The user can say: add quote: "Your quote here". This action extracts the quoted
    text naively and stores it locally. Robustness is provided with basic parsing
    and safe file writes.
    """

    def name(self) -> Text:
        return "action_add_quote"

    @staticmethod
    def _extract_quoted_text(message: str) -> str:
        # Look for the first quoted segment; supports both straight and curly quotes
        candidates = []
        pairs = [("\"", "\""), ("“", "”"), ("'", "'")]
        for left, right in pairs:
            if left in message and right in message:
                try:
                    start = message.index(left) + len(left)
                    end = message.index(right, start)
                    candidates.append(message[start:end].strip())
                except ValueError:
                    continue
        # Prefer the longest candidate as the most likely full quote
        return max(candidates, key=len) if candidates else message.strip()

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user_text = tracker.latest_message.get("text", "").strip()
        extracted = self._extract_quoted_text(user_text)
        if not extracted:
            dispatcher.utter_message(text="I didn't catch the quote text. Try: add quote: \"Your quote here\"")
            return []

        quotes = _load_quotes()
        entry = {"text": extracted, "author": "(you)"}
        quotes.append(entry)
        try:
            _save_quotes(quotes)
            dispatcher.utter_message(response="utter_ack_add")
            formatted = f"\"{extracted}\" — (you)"
            return [SlotSet("last_quote", formatted)]
        except Exception as e:
            dispatcher.utter_message(text=f"I couldn't save the quote due to a file error. Still, I remember it for this session.")
            formatted = f"\"{extracted}\" — (you)"
            return [SlotSet("last_quote", formatted)]


class ActionShowLastQuote(Action):
    """Speak back the last quote saved in slot last_quote, with a graceful fallback."""

    def name(self) -> Text:
        return "action_show_last_quote"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        last = tracker.get_slot("last_quote")
        if last:
            dispatcher.utter_message(text=last)
        else:
            dispatcher.utter_message(text="I don't have a last quote yet. Ask me for a quote or add your own.")
        return []


class ActionFetchQuoteApi(Action):
    """Fetch a quote from a public API with timeout and offline fallback to local quotes.

    Uses https://zenquotes.io/api/random without any API key. If network fails or
    the response is invalid, fall back to local quotes. Always sets last_quote.
    """

    def name(self) -> Text:
        return "action_fetch_quote_api"

    def _fetch_remote(self) -> Dict[str, str]:
        try:
            response = requests.get("https://zenquotes.io/api/random", timeout=4)
            response.raise_for_status()
            data = response.json()
            # Expected shape: [{"q": "quote", "a": "author"}]
            if isinstance(data, list) and data and isinstance(data[0], dict):
                quote_text = data[0].get("q") or ""
                author = data[0].get("a") or "Unknown"
                if quote_text:
                    return {"text": quote_text, "author": author}
        except Exception:
            pass
        return {}

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        remote = self._fetch_remote()
        if remote:
            message = f"\"{remote['text']}\" — {remote.get('author', 'Unknown')}"
            dispatcher.utter_message(text=message)
            return [SlotSet("last_quote", message)]

        # Fallback to local quotes if remote failed
        quotes = _load_quotes()
        index = (len(tracker.events) or 0) % len(quotes)
        quote = quotes[index]
        text = quote.get("text", "Here's a quote.")
        author = quote.get("author", "Unknown")
        message = f"(offline) \"{text}\" — {author}"
        dispatcher.utter_message(text=message)
        return [SlotSet("last_quote", message)]
