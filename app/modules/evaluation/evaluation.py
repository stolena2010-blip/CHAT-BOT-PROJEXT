"""
Evaluation Module
-----------------
Evaluates the multi-agent system against the labeled SMS conversations dataset.
For each recruiter turn with a label (continue/schedule/end), the system predicts
what action it would take, then compares against the ground truth.

Metrics:
 • Accuracy
 • Confusion Matrix
"""

import json
import os
from collections import defaultdict
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from dotenv import load_dotenv

from app.modules.agents.exit_advisor import should_end_conversation
from app.modules.agents.main_agent import MainAgent

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))
CONVERSATIONS_PATH = os.path.join(PROJECT_ROOT, "sms_conversations.json")


def load_test_data() -> list[dict]:
    """
    Extract test examples from labeled conversations.
    Returns list of dict with keys:
      conversation_id, history, candidate_message, true_label
    """
    with open(CONVERSATIONS_PATH, "r", encoding="utf-8") as f:
        conversations = json.load(f)

    examples = []
    for conv in conversations:
        turns = conv["turns"]
        history_lines = []
        reference_date = conv.get("start_time_utc", "")[:10]

        for i, turn in enumerate(turns):
            if turn["speaker"] == "recruiter" and turn.get("label"):
                candidate_msg = ""
                if i > 0 and turns[i - 1]["speaker"] == "candidate":
                    candidate_msg = turns[i - 1]["text"]

                examples.append({
                    "conversation_id": conv["conversation_id"],
                    "history": "\n".join(history_lines) if history_lines else "(start)",
                    "candidate_message": candidate_msg,
                    "true_label": turn["label"],
                    "reference_date": reference_date,
                })

            speaker = turn["speaker"].capitalize()
            history_lines.append(f"{speaker}: {turn['text']}")

    return examples


def evaluate_system(
    fine_tuned_model: str | None = None,
    verbose: bool = True,
) -> dict:
    """
    Run prediction on all test examples and compute metrics.
    Returns dict with accuracy, predictions, true_labels, and confusion_matrix.
    """
    examples = load_test_data()
    agent = MainAgent(fine_tuned_exit_model=fine_tuned_model)

    true_labels = []
    predicted_labels = []
    results = []

    for i, ex in enumerate(examples):
        if verbose:
            print(f"[Eval] Processing {i + 1}/{len(examples)} "
                  f"(conv {ex['conversation_id']})")

        # Reset agent and set history
        agent.reset()

        # Get the system's decision
        should_end = should_end_conversation(
            candidate_message=ex["candidate_message"],
            conversation_history=ex["history"],
            fine_tuned_model=fine_tuned_model,
        )

        # Use the Main Agent's full decision prompt for accurate evaluation
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        exit_rec = "end" if should_end else "continue"
        decision_prompt = ChatPromptTemplate.from_template(
            """You are the Main Agent of an SMS recruitment chatbot for a Python Developer position.
You must decide what the RECRUITER's next action should be.

DEFINITIONS:
- "continue" — The recruiter asks follow-up questions about the candidate's skills,
  answers candidate questions about the role/company, or provides information.
  This is for information-gathering and Q&A phases.
- "schedule" — The recruiter proposes specific interview date/time slots,
  confirms a time the candidate suggested, or offers alternative times
  after a rejection. If the candidate has shown enough interest and experience
  has been discussed, the recruiter should move to scheduling.
- "end" — The recruiter wraps up the conversation because:
  * An interview was successfully confirmed
  * The candidate explicitly said they're not interested
  * The candidate asked to stop contact

EXAMPLES:

Example 1:
Conversation: Recruiter asked about experience. Candidate: "I have 5 years with Python and Django"
→ schedule (candidate is qualified, time to propose interview)

Example 2:
Conversation: Recruiter proposed Wed 10AM or Thu 2PM. Candidate: "Those don't work for me"
→ schedule (need to offer alternative times)

Example 3:
Conversation: Candidate: "What technologies does the stack use?"
→ continue (answering a question, still in info phase)

Example 4:
Conversation: Recruiter confirmed interview. Candidate: "Sounds great, see you then"
→ end (interview booked, conversation done)

Example 5:
Conversation: Candidate: "Please remove me from your list"
→ end (candidate not interested)

Example 6:
Conversation: Recruiter asked about Python. Candidate: "I have 3 years with Django and Flask."
→ schedule (basic qualification established, move to scheduling)

Exit Advisor recommendation: {exit_recommendation}

Conversation so far:
{conversation_history}

Candidate's latest message:
{candidate_message}

What should the recruiter do next? Respond with ONLY one word: "continue", "schedule", or "end"."""
        )
        chain = decision_prompt | agent.llm | StrOutputParser()
        raw_prediction = chain.invoke({
            "exit_recommendation": exit_rec,
            "conversation_history": ex["history"],
            "candidate_message": ex["candidate_message"],
        }).strip().lower()

        # Normalize
        if "end" in raw_prediction:
            prediction = "end"
        elif "schedule" in raw_prediction:
            prediction = "schedule"
        else:
            prediction = "continue"

        true_labels.append(ex["true_label"])
        predicted_labels.append(prediction)
        results.append({
            "conversation_id": ex["conversation_id"],
            "true_label": ex["true_label"],
            "predicted": prediction,
            "correct": ex["true_label"] == prediction,
            "candidate_msg": ex["candidate_message"][:80],
        })

    # Compute metrics
    labels = ["continue", "schedule", "end"]
    acc = accuracy_score(true_labels, predicted_labels)
    cm = confusion_matrix(true_labels, predicted_labels, labels=labels)
    report = classification_report(
        true_labels, predicted_labels, labels=labels, output_dict=True
    )

    if verbose:
        print(f"\n{'=' * 50}")
        print(f"Accuracy: {acc:.2%}")
        print(f"{'=' * 50}")
        print(classification_report(true_labels, predicted_labels, labels=labels))

    return {
        "accuracy": acc,
        "confusion_matrix": cm,
        "classification_report": report,
        "true_labels": true_labels,
        "predicted_labels": predicted_labels,
        "detailed_results": results,
    }


def plot_confusion_matrix(cm, labels=None, save_path=None):
    """Plot and optionally save a confusion matrix heatmap."""
    if labels is None:
        labels = ["continue", "schedule", "end"]

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion Matrix — Multi-Agent Recruitment Chatbot")
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"[Eval] Saved confusion matrix to {save_path}")

    return fig


# ── Run directly ──────────────────────────────────────────────────────
if __name__ == "__main__":
    results = evaluate_system()
    plot_confusion_matrix(
        results["confusion_matrix"],
        save_path=os.path.join(PROJECT_ROOT, "confusion_matrix.png"),
    )
    plt.show()
