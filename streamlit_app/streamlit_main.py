"""
Streamlit Main App
------------------
SMS-style chat interface for the recruitment chatbot PoC.
Replaces actual SMS with a web-based chat UI.
"""

import sys
import os

# Ensure project root is on path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from app.modules.agents.main_agent import MainAgent


def init_session_state():
    """Initialize Streamlit session state variables."""
    if "agent" not in st.session_state:
        st.session_state.agent = MainAgent()
    if "messages" not in st.session_state:
        opening = (
            "Hi, thanks for submitting your application for our "
            "Python Developer role. Could you share a bit about "
            "your Python experience?"
        )
        st.session_state.messages = [
            {"role": "recruiter", "content": opening}
        ]
        st.session_state.agent.conversation_history = [
            {"speaker": "recruiter", "text": opening}
        ]
    if "conversation_ended" not in st.session_state:
        st.session_state.conversation_ended = False


def reset_conversation():
    """Reset the conversation to start fresh."""
    st.session_state.agent.reset()
    opening = (
        "Hi, thanks for submitting your application for our "
        "Python Developer role. Could you share a bit about "
        "your Python experience?"
    )
    st.session_state.messages = [
        {"role": "recruiter", "content": opening}
    ]
    st.session_state.agent.conversation_history = [
        {"speaker": "recruiter", "text": opening}
    ]
    st.session_state.conversation_ended = False


def main():
    st.set_page_config(
        page_title="Recruitment Chatbot",
        page_icon="💬",
        layout="centered",
    )

    st.title("💬 SMS Recruitment Chatbot")
    st.caption("Python Developer Position — Proof of Concept")

    init_session_state()

    # Sidebar
    with st.sidebar:
        st.header("Controls")
        if st.button("🔄 New Conversation", use_container_width=True):
            reset_conversation()
            st.rerun()

        st.divider()
        st.markdown("**How it works:**")
        st.markdown(
            "1. The bot asks about your experience\n"
            "2. You can ask questions about the role\n"
            "3. When ready, it schedules an interview\n"
            "4. If you're not interested, it ends politely"
        )

        st.divider()
        st.markdown("**Agent Architecture:**")
        st.markdown(
            "- 🧠 **Main Agent** — orchestrator\n"
            "- 📋 **Info Advisor** — answers questions (RAG)\n"
            "- 📅 **Scheduling Advisor** — finds slots (SQL)\n"
            "- 🚪 **Exit Advisor** — detects disinterest"
        )

    # Display chat messages
    for msg in st.session_state.messages:
        role = msg["role"]
        if role == "recruiter":
            with st.chat_message("assistant", avatar="🤖"):
                st.write(msg["content"])
        else:
            with st.chat_message("user", avatar="👤"):
                st.write(msg["content"])

    # Chat input
    if st.session_state.conversation_ended:
        st.info("Conversation ended. Click '🔄 New Conversation' to start again.")
    else:
        if prompt := st.chat_input("Type your message..."):
            # Show user message
            st.session_state.messages.append(
                {"role": "candidate", "content": prompt}
            )
            with st.chat_message("user", avatar="👤"):
                st.write(prompt)

            # Get agent response
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    result = st.session_state.agent.process_message(prompt)

                st.write(result["response"])
                st.caption(f"Action: {result['action']}")

            st.session_state.messages.append(
                {"role": "recruiter", "content": result["response"]}
            )

            if result["action"] == "end":
                st.session_state.conversation_ended = True
                st.rerun()


if __name__ == "__main__":
    main()
