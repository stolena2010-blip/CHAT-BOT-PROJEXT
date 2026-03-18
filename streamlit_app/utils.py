"""Helper functions for Streamlit components."""

import json
import os


def load_conversations(path: str | None = None) -> list[dict]:
    """Load the labeled SMS conversations dataset."""
    if path is None:
        path = os.path.join(
            os.path.dirname(__file__), "..", "sms_conversations.json"
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_conversation(conversation: dict) -> str:
    """Format a conversation dict as readable text."""
    lines = [f"Conversation {conversation['conversation_id']}:"]
    for turn in conversation["turns"]:
        speaker = turn["speaker"].capitalize()
        label = f" [{turn['label']}]" if turn.get("label") else ""
        lines.append(f"  {speaker}: {turn['text']}{label}")
    return "\n".join(lines)
