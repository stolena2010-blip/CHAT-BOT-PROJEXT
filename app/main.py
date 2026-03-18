"""
main.py — Entry point of the application
-----------------------------------------
Demonstrates the multi-agent recruitment chatbot in CLI mode.
For the web UI, use streamlit_app/streamlit_main.py instead.
"""

from app.modules.agents.main_agent import MainAgent


def run_cli():
    """Run the chatbot in interactive CLI mode."""
    print("=" * 60)
    print("  SMS Recruitment Chatbot — Python Developer Position")
    print("  Type 'quit' to exit, 'reset' to start a new conversation")
    print("=" * 60)

    agent = MainAgent()

    # Start conversation with an opening message
    opening = (
        "Hi, thanks for submitting your application for our "
        "Python Developer role. Could you share a bit about "
        "your Python experience?"
    )
    print(f"\nRecruiter: {opening}")
    agent.conversation_history.append(
        {"speaker": "recruiter", "text": opening}
    )

    while True:
        user_input = input("\nCandidate: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "reset":
            agent.reset()
            print(f"\nRecruiter: {opening}")
            agent.conversation_history.append(
                {"speaker": "recruiter", "text": opening}
            )
            continue

        result = agent.process_message(user_input)
        print(f"\nRecruiter: {result['response']}")
        print(f"  [action: {result['action']}]")

        if result["action"] == "end":
            print("\n--- Conversation ended ---")
            break


if __name__ == "__main__":
    run_cli()
