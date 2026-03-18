"""
Main Agent — Conversation Orchestrator
---------------------------------------
Manages the dialogue with the candidate turn-by-turn.
At each turn it consults the three advisors and decides:
  • continue  — keep talking / ask more / answer questions
  • schedule  — propose or confirm interview time slots
  • end       — politely close the conversation

Architecture:
  Candidate msg → Main Agent → consult advisors → pick action → generate response
"""

import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

from app.modules.agents.exit_advisor import should_end_conversation
from app.modules.agents.scheduling_advisor import ask_scheduling_advisor
from app.modules.agents.info_advisor import ask_info_advisor

load_dotenv()

# ── Prompts ────────────────────────────────────────────────────────────

DECISION_PROMPT = """You are the Main Agent of an SMS-based recruitment chatbot
for a Python Developer position.

Your job is to analyze the conversation and decide the NEXT ACTION.

Rules:
1. If the candidate seems uninterested, wants to stop, or the interview is
   already booked → choose "end"
2. If the conversation context suggests it's time to schedule an interview
   (candidate is interested, qualifications discussed) → choose "schedule"
3. Otherwise → choose "continue" (ask questions, answer queries, keep engaging)

Exit Advisor recommendation: {exit_recommendation}

Conversation history:
{conversation_history}

Candidate's latest message:
{candidate_message}

Respond with ONLY one word: "continue", "schedule", or "end"."""

RESPONSE_PROMPT = """You are a friendly, professional recruitment chatbot
for a Python Developer position. Generate the next SMS response to the candidate.

Action decided: {action}
Advisor suggestion: {advisor_response}

Conversation history:
{conversation_history}

Candidate's latest message:
{candidate_message}

Guidelines:
- Keep messages short (SMS-friendly, 1-3 sentences).
- Be warm and professional.
- If action is "schedule": propose time slots or confirm booking.
- If action is "end": close politely.
- If action is "continue": keep the conversation going, answer questions,
  or ask relevant follow-ups about their experience.

Your SMS response:"""


class MainAgent:
    """Orchestrates the multi-agent recruitment chatbot."""

    def __init__(self, fine_tuned_exit_model: str | None = None):
        self.fine_tuned_exit_model = fine_tuned_exit_model or os.getenv(
            "FINE_TUNED_EXIT_MODEL"
        )
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.conversation_history: list[dict] = []

    def _format_history(self) -> str:
        if not self.conversation_history:
            return "(start of conversation)"
        return "\n".join(
            f"{turn['speaker'].capitalize()}: {turn['text']}"
            for turn in self.conversation_history
        )

    def _decide_action(
        self, candidate_message: str, exit_recommendation: str
    ) -> str:
        """Use LLM to decide: continue / schedule / end."""
        prompt = ChatPromptTemplate.from_template(DECISION_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({
            "exit_recommendation": exit_recommendation,
            "conversation_history": self._format_history(),
            "candidate_message": candidate_message,
        })
        decision = result.strip().lower()
        # Normalize to valid actions
        if "end" in decision:
            return "end"
        if "schedule" in decision:
            return "schedule"
        return "continue"

    def _get_advisor_response(
        self,
        action: str,
        candidate_message: str,
        reference_date: str | None = None,
    ) -> str:
        """Route to the appropriate advisor based on the decided action."""
        history = self._format_history()

        if action == "schedule":
            return ask_scheduling_advisor(
                candidate_message=candidate_message,
                conversation_history=history,
                reference_date=reference_date,
            )
        elif action == "continue":
            try:
                return ask_info_advisor(
                    candidate_message=candidate_message,
                    conversation_history=history,
                )
            except Exception:
                # If ChromaDB not built yet, skip RAG
                return ""
        else:  # end
            return "The conversation should be concluded politely."

    def _generate_response(
        self, action: str, advisor_response: str, candidate_message: str
    ) -> str:
        """Generate the final SMS response using the action and advisor input."""
        prompt = ChatPromptTemplate.from_template(RESPONSE_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({
            "action": action,
            "advisor_response": advisor_response,
            "conversation_history": self._format_history(),
            "candidate_message": candidate_message,
        })

    def process_message(
        self,
        candidate_message: str,
        reference_date: str | None = None,
    ) -> dict:
        """
        Process a single candidate message. Returns:
        {
            "action": "continue" | "schedule" | "end",
            "response": "...",
        }
        """
        # 1. Consult Exit Advisor
        should_end = should_end_conversation(
            candidate_message=candidate_message,
            conversation_history=self._format_history(),
            fine_tuned_model=self.fine_tuned_exit_model,
        )
        exit_rec = "end" if should_end else "continue"

        # 2. Decide action
        action = self._decide_action(candidate_message, exit_rec)

        # 3. Get advisor input
        advisor_response = self._get_advisor_response(
            action, candidate_message, reference_date
        )

        # 4. Generate response
        response = self._generate_response(action, advisor_response, candidate_message)

        # 5. Update history
        self.conversation_history.append(
            {"speaker": "candidate", "text": candidate_message}
        )
        self.conversation_history.append(
            {"speaker": "recruiter", "text": response}
        )

        return {"action": action, "response": response}

    def reset(self):
        """Clear conversation history."""
        self.conversation_history = []

    def set_history(self, history: list[dict]):
        """Set conversation history from external source."""
        self.conversation_history = history.copy()
