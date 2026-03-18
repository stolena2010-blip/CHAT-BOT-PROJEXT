"""
Exit Advisor Agent
------------------
Evaluates whether it is appropriate to end the conversation.
Detects disinterest signals (e.g. "already found a job", "stop texting me")
so uninterested candidates aren't unnecessarily followed up with.

This advisor has two modes:
 • Base mode:       Uses a prompted GPT-4o model.
 • Fine-tuned mode: Uses a fine-tuned model (after running fine_tuning module).
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

EXIT_ADVISOR_SYSTEM_PROMPT = """You are the Exit Advisor for a recruitment chatbot.

Analyze the conversation and the candidate's latest message to determine
whether the conversation should END.

The conversation should END if:
- The candidate explicitly says they are not interested (e.g. "remove me from your list")
- The candidate says they already found a job
- The candidate asks to stop being contacted
- The candidate repeatedly declines all proposed interview times
- An interview has been successfully booked and confirmed
- The conversation has naturally concluded

The conversation should CONTINUE if:
- The candidate is still engaged and asking questions
- The candidate is considering but hasn't decided
- There's still an active scheduling discussion

Conversation history:
{conversation_history}

Candidate's latest message:
{candidate_message}

Respond with ONLY one of these two words:
- "end" — if the conversation should end
- "continue" — if the conversation should continue

Your answer:"""


def get_exit_advisor_chain(fine_tuned_model: str | None = None):
    """
    Build the Exit Advisor chain.
    If fine_tuned_model is provided (e.g. "ft:gpt-4o-mini-2024-07-18:..."),
    use the fine-tuned model instead of the base prompt.
    """
    model_name = fine_tuned_model or "gpt-4o"

    llm = ChatOpenAI(
        model=model_name,
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    prompt = ChatPromptTemplate.from_template(EXIT_ADVISOR_SYSTEM_PROMPT)
    chain = prompt | llm | StrOutputParser()
    return chain


def should_end_conversation(
    candidate_message: str,
    conversation_history: str,
    fine_tuned_model: str | None = None,
) -> bool:
    """
    Ask the Exit Advisor whether the conversation should end.
    Returns True if the advisor recommends ending.
    """
    chain = get_exit_advisor_chain(fine_tuned_model)
    result = chain.invoke({
        "conversation_history": conversation_history,
        "candidate_message": candidate_message,
    })
    return result.strip().lower() == "end"
