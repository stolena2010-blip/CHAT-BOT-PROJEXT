"""
Info Advisor Agent
------------------
Answers candidate questions about the Python Developer position by
retrieving relevant context from the ChromaDB vector store (RAG).
Also formulates engaging responses to keep the conversation moving
toward scheduling an interview.
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

from app.modules.embedding.embedding import get_vector_store

load_dotenv()

INFO_ADVISOR_SYSTEM_PROMPT = """You are the Info Advisor for Hell Corp's recruitment chatbot 🔥.
Your role is to answer candidate questions about the Python Developer position
accurately, using ONLY the context provided from the job description.

Guidelines:
- Give thorough, informative answers (not just one line)
- After answering, ask: "Is there anything else you'd like to know?"
- Keep the conversation warm with a touch of devilish humor
- If the context doesn't contain the answer, say so honestly and suggest
  discussing it during the interview — "we'll cover that in person,
  we don't bite... much 😈"
- Do NOT invent information not found in the context

Context from the job description:
{context}

Conversation so far:
{conversation_history}

Candidate's latest message:
{candidate_message}

Provide a helpful, detailed response (2-3 sentences)."""


def get_info_advisor_chain():
    """Build and return the Info Advisor LangChain chain."""
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    prompt = ChatPromptTemplate.from_template(INFO_ADVISOR_SYSTEM_PROMPT)
    chain = prompt | llm | StrOutputParser()
    return chain


def ask_info_advisor(
    candidate_message: str,
    conversation_history: str,
) -> str:
    """
    Query the Info Advisor: retrieves relevant job-description context
    from ChromaDB and generates a response.
    """
    # Retrieve context from vector store
    vector_store = get_vector_store()
    docs = vector_store.similarity_search(candidate_message, k=3)
    context = "\n\n".join(doc.page_content for doc in docs)

    chain = get_info_advisor_chain()
    response = chain.invoke({
        "context": context,
        "conversation_history": conversation_history,
        "candidate_message": candidate_message,
    })
    return response
