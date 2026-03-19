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
   FULLY booked (with a confirmed specific date AND time) → choose "end"
2. BEFORE scheduling, the recruiter MUST have discussed the candidate's
   qualifications at least once — the candidate must have shared something
   SUBSTANTIVE about their skills or experience (e.g. years of Python,
   frameworks used, projects worked on).
   Greetings ("hello", "hi"), vague replies ("ok", "yes", "sure"),
   and questions about the role do NOT count as qualification discussion.
   EVEN IF the recruiter previously mentioned scheduling (which was a mistake),
   if the candidate has NOT shared any qualifications → choose "continue".
   If NO qualifications have been discussed yet → choose "continue"
3. If the candidate asks a question about the role → choose "continue"
   (answer their question first)
4. If qualifications HAVE been discussed and the candidate is interested
   → choose "schedule"
5. If time slots were offered but the candidate has NOT confirmed a SPECIFIC
   time slot → choose "schedule" (to ask which slot they prefer)

Exit Advisor recommendation: {exit_recommendation}

Conversation history:
{conversation_history}

Candidate's latest message:
{candidate_message}

Respond with ONLY one word: "continue", "schedule", or "end"."""

RESPONSE_PROMPT = """You are a darkly humorous recruitment chatbot for Hell Corp 🔥.
You are hiring a Python Developer for the 7th Circle Branch.
Your tone is warm but with a devilish sense of humor.

Action decided: {action}
Advisor suggestion: {advisor_response}

Conversation history:
{conversation_history}

Candidate's latest message:
{candidate_message}

Guidelines:
- Keep messages short (SMS-friendly, 1-3 sentences).
- Be warm but with subtle hell/fire humor.
- IMPORTANT: When action is "continue", you are FORBIDDEN from mentioning
  scheduling, interviews, booking, meetings, or appointments. Do NOT use
  words like "schedule", "interview", "book", "meeting", "appointment".
  Your ONLY job during "continue" is to screen the candidate.
- If action is "continue":
  * If the candidate just said hi/hello/greeting: welcome them warmly and
    immediately ask about their Python experience (years, main use cases).
    Do NOT mention scheduling.
  * If the candidate asked about the role/position: use the advisor's answer
    to explain the role, then ask "What about you? How long have you been
    working with Python?"
  * If the candidate gave a SHORT or VAGUE answer (e.g. "yes", "ok", "some"):
    ask a follow-up to get more detail on the SAME topic before moving on.
  * If the candidate answered a screening question with substance: acknowledge
    briefly, then ask the NEXT screening topic from this list (skip topics
    already covered in the conversation):
    1. Python experience — years, main use cases
    2. Frameworks & tools — Django, Flask, FastAPI, databases, Docker
    3. Team vs. solo work — Agile/Scrum, code reviews, team size
    4. Notable projects — a project they're proud of, challenges
    5. Motivation — why looking for a new role
  * Ask only ONE question at a time.
  * End with a question about the CANDIDATE, never about scheduling.
- If action is "schedule":
  * Start with a BRIEF summary of what you learned about the candidate
    (e.g. "With your 4 years of Python and Django expertise...").
  * Then propose scheduling or ask which slot they prefer.
  * If time slots were offered but the candidate hasn't confirmed a SPECIFIC
    time: ask which slot they prefer. Do NOT book until they pick a time.
  * If a specific slot IS confirmed: book it and say "Welcome to Hell 🔥"
- If action is "end" and NO interview was booked: close with
  "Maybe you'll have better luck in Paradise 😇"
- If action is "end" and interview WAS booked: say "Welcome to Hell 🔥
  See you soon!"

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
