"""
Streamlit Main App
------------------
SMS-style chat interface for the recruitment chatbot PoC.
Hell Corp themed — 7th Circle Branch 🔥
"""

import sys
import os

# Ensure project root is on path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from app.modules.agents.main_agent import MainAgent

# ── Hell Corp Custom CSS ────────────────────────────────────────────────
HELL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Creepster&family=Cinzel:wght@400;700&display=swap');

/* Dark fiery background */
.stApp {
    background: linear-gradient(180deg, #1a0a0a 0%, #2d0a0a 40%, #3d1111 100%);
}

/* Main title */
h1 {
    font-family: 'Creepster', cursive !important;
    color: #ff4500 !important;
    text-shadow: 0 0 20px #ff4500, 0 0 40px #ff2200, 0 0 60px #cc0000;
    font-size: 3rem !important;
    text-align: center;
}

/* Subtitle / caption */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #ff8c00 !important;
    font-family: 'Cinzel', serif !important;
    text-align: center;
    font-size: 1.1rem !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a0505 0%, #2a0808 100%);
    border-right: 2px solid #ff4500;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] .stMarkdown h2 {
    color: #ff6347 !important;
    font-family: 'Cinzel', serif !important;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] li,
section[data-testid="stSidebar"] .stMarkdown {
    color: #ffaa88 !important;
}

/* Chat messages — recruiter (assistant) */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: linear-gradient(135deg, #3d0c0c 0%, #4a1515 100%) !important;
    border: 1px solid #ff450055;
    border-radius: 12px;
    box-shadow: 0 0 15px rgba(255, 69, 0, 0.2);
}

/* Chat messages — user */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
    border: 1px solid #444;
    border-radius: 12px;
}

/* All chat text */
[data-testid="stChatMessage"] p {
    color: #ffe0cc !important;
    font-size: 1.05rem;
}

/* Info box when conversation ends */
[data-testid="stAlert"] {
    background: linear-gradient(135deg, #4a1515, #2d0a0a) !important;
    border: 1px solid #ff4500 !important;
    color: #ff8c00 !important;
}

/* Chat input */
[data-testid="stChatInput"] textarea {
    background: #2d0a0a !important;
    color: #ffe0cc !important;
    border: 1px solid #ff450066 !important;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, #8b0000, #ff4500) !important;
    color: white !important;
    border: none !important;
    font-family: 'Cinzel', serif !important;
    font-weight: bold;
    box-shadow: 0 0 10px rgba(255, 69, 0, 0.4);
    transition: all 0.3s;
}

.stButton > button:hover {
    box-shadow: 0 0 25px rgba(255, 69, 0, 0.8);
    transform: scale(1.02);
}

/* Divider */
hr {
    border-color: #ff450044 !important;
}

/* Caption under messages */
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] {
    color: #ff6347 !important;
}

/* Spinner */
.stSpinner > div {
    color: #ff4500 !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-track {
    background: #1a0a0a;
}
::-webkit-scrollbar-thumb {
    background: #ff4500;
    border-radius: 4px;
}
</style>
"""

HELL_HEADER_HTML = """
<div style="text-align: center; padding: 10px 0 5px 0;">
    <span style="font-size: 4rem;">😈</span>
    <div style="font-family: 'Cinzel', serif; color: #ff6347; font-size: 0.9rem;
                letter-spacing: 3px; margin-top: -5px;">
        ABANDON ALL HOPE, YE WHO ENTER HERE
    </div>
</div>
"""


def init_session_state():
    """Initialize Streamlit session state variables."""
    if "agent" not in st.session_state:
        st.session_state.agent = MainAgent()
    if "messages" not in st.session_state:
        opening = (
            "Welcome, mortal! 🔥 Hell Corp is looking for a "
            "Python Developer for our 7th Circle Branch. "
            "Could you share a bit about your Python experience?"
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
        "Welcome, mortal! 🔥 Hell Corp is looking for a "
        "Python Developer for our 7th Circle Branch. "
        "Could you share a bit about your Python experience?"
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
        page_title="Hell Corp Recruitment 🔥",
        page_icon="🔥",
        layout="centered",
    )

    # Inject Hell theme
    st.markdown(HELL_CSS, unsafe_allow_html=True)
    st.markdown(HELL_HEADER_HTML, unsafe_allow_html=True)

    st.title("🔥 Hell Corp — Recruitment Chatbot")
    st.caption("Python Developer Position — 7th Circle Branch")

    init_session_state()

    # Sidebar
    with st.sidebar:
        st.markdown(
            '<div style="text-align:center; font-size:3rem; padding:10px 0;">'
            '👹</div>',
            unsafe_allow_html=True,
        )
        st.header("⚙️ Controls")
        if st.button("🔥 New Conversation", use_container_width=True):
            reset_conversation()
            st.rerun()

        st.divider()
        st.markdown("**📜 How it works:**")
        st.markdown(
            "1. 😈 The bot asks about your experience\n"
            "2. 🔥 You can ask questions about the role\n"
            "3. 📅 When ready, it schedules an interview\n"
            "4. 😇 If you're not interested, it ends... mercifully"
        )

        st.divider()
        st.markdown("**🏗️ Agent Architecture:**")
        st.markdown(
            "- 😈 **Main Agent** — the Devil's orchestrator\n"
            "- 📋 **Info Advisor** — Hell's knowledge keeper (RAG)\n"
            "- 📅 **Scheduling Advisor** — books your descent (SQL)\n"
            "- 🚪 **Exit Advisor** — detects cowardice"
        )

        st.divider()
        st.markdown(
            '<div style="text-align:center; color:#ff6347; font-size:0.8rem; '
            'font-family: Cinzel, serif;">'
            '© Hell Corp Ltd.<br>7th Circle Branch<br>Est. ♾️ BC'
            '</div>',
            unsafe_allow_html=True,
        )

    # Display chat messages
    for msg in st.session_state.messages:
        role = msg["role"]
        if role == "recruiter":
            with st.chat_message("assistant", avatar="😈"):
                st.write(msg["content"])
        else:
            with st.chat_message("user", avatar="🧑"):
                st.write(msg["content"])

    # Chat input
    if st.session_state.conversation_ended:
        st.markdown(
            '<div style="text-align:center; padding:20px; '
            'background: linear-gradient(135deg, #4a1515, #2d0a0a); '
            'border: 1px solid #ff4500; border-radius: 10px; '
            'color: #ff8c00; font-family: Cinzel, serif; font-size: 1.1rem;">'
            '🔥 Conversation ended. Click <b>🔥 New Conversation</b> '
            'to summon another soul. 🔥</div>',
            unsafe_allow_html=True,
        )
    else:
        if prompt := st.chat_input("Speak, mortal... 🔥"):
            # Show user message
            st.session_state.messages.append(
                {"role": "candidate", "content": prompt}
            )
            with st.chat_message("user", avatar="🧑"):
                st.write(prompt)

            # Get agent response
            with st.chat_message("assistant", avatar="😈"):
                with st.spinner("Consulting the underworld... 🔥"):
                    result = st.session_state.agent.process_message(prompt)

                st.write(result["response"])
                action_icons = {
                    "continue": "🔥",
                    "schedule": "📅",
                    "end": "💀",
                }
                icon = action_icons.get(result["action"], "")
                st.caption(f"{icon} Action: {result['action']}")

            st.session_state.messages.append(
                {"role": "recruiter", "content": result["response"]}
            )

            if result["action"] == "end":
                st.session_state.conversation_ended = True
                st.rerun()


if __name__ == "__main__":
    main()
