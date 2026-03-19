"""
Scheduling Advisor Agent
------------------------
Determines whether it's the right time to schedule an interview, and
interacts with the SQL database via OpenAI Function Calling to find
available time slots.

Key behavior:
 • Parses relative date expressions from the conversation (e.g. "next Friday")
   using the conversation's timestamp as the reference date.
 • Returns the 3 nearest available slots to suggest to the candidate.
 • Can confirm/book a specific slot once the candidate agrees.
"""

import json
import os
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from dotenv import load_dotenv

from app.modules.database.database import (
    get_available_slots,
    check_slot_available,
    book_slot,
)

load_dotenv()

# ── OpenAI Function Calling tool definitions ──────────────────────────

SCHEDULE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_available_slots",
            "description": (
                "Get available interview time slots for a given position "
                "within a date range. Returns up to 3 nearest slots."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "position": {
                        "type": "string",
                        "description": "Job position, e.g. 'Python Dev'",
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format",
                    },
                    "to_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format",
                    },
                },
                "required": ["position", "from_date", "to_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_slot_available",
            "description": "Check if a specific date and time slot is available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "position": {"type": "string"},
                    "slot_date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    },
                    "slot_time": {
                        "type": "string",
                        "description": "Time in HH:MM format",
                    },
                },
                "required": ["position", "slot_date", "slot_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_slot",
            "description": "Book (reserve) a specific interview slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "position": {"type": "string"},
                    "slot_date": {"type": "string"},
                    "slot_time": {"type": "string"},
                },
                "required": ["position", "slot_date", "slot_time"],
            },
        },
    },
]

# Map function names to actual Python callables
_TOOL_MAP = {
    "get_available_slots": get_available_slots,
    "check_slot_available": check_slot_available,
    "book_slot": book_slot,
}

SCHEDULING_SYSTEM_PROMPT = """You are the Scheduling Advisor for Hell Corp's recruitment chatbot 🔥.

Today's date (reference) is: {reference_date}

Your responsibilities:
1. Analyze the conversation to determine if it's appropriate to schedule now.
2. When the candidate mentions a date/time (even relative like "next Friday"),
   convert it to an absolute YYYY-MM-DD date using the reference date above.
3. Use the provided tools to find available slots and suggest the 3 nearest ones.
4. CONFIRMATION STEP: When the candidate picks a slot, DO NOT book immediately.
   First confirm: "Just to confirm — [date] at [time]. Shall I lock it in? 🔥"
   Only call book_slot AFTER the candidate explicitly confirms (e.g. "yes",
   "confirm", "book it", "sounds good").
5. If the candidate picks a time NOT in the offered list, do NOT book or
   confirm it. Instead, remind them of the available slots and ask to choose
   from those.
6. If the candidate's preferred time is unavailable, suggest the nearest
   available alternatives and ask which one works.

IMPORTANT RULES:
- The position is always "Python Dev".
- Available days are Tue–Fri and Sunday only (no Saturday or Monday —
  even demons need rest).
- Hours are 09:00–17:00.
- When searching, look within a 14-day window from the reference date.
- Be concise with a hint of fire humor.

Conversation so far:
{conversation_history}

Candidate's latest message:
{candidate_message}

Decide what to do and use the tools if needed."""


def ask_scheduling_advisor(
    candidate_message: str,
    conversation_history: str,
    reference_date: str | None = None,
) -> str:
    """
    Run the Scheduling Advisor with function calling.
    reference_date: YYYY-MM-DD string or None (defaults to today).
    """
    if reference_date is None:
        reference_date = datetime.now().strftime("%Y-%m-%d")

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    messages = [
        SystemMessage(content=SCHEDULING_SYSTEM_PROMPT.format(
            reference_date=reference_date,
            conversation_history=conversation_history,
            candidate_message=candidate_message,
        )),
        HumanMessage(content=candidate_message),
    ]

    # Iterative tool-calling loop
    for _ in range(5):  # safety limit
        response = llm.invoke(messages, tools=SCHEDULE_TOOLS)

        if not response.tool_calls:
            return response.content

        # Append the assistant message with tool_calls once
        messages.append(response)

        # Execute each tool call and append ToolMessage with matching id
        for tool_call in response.tool_calls:
            func_name = tool_call["name"]
            func_args = tool_call["args"]
            result = _TOOL_MAP[func_name](**func_args)

            messages.append(
                ToolMessage(
                    content=json.dumps(result, default=str),
                    tool_call_id=tool_call["id"],
                )
            )

    return response.content
