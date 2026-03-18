"""
Fine-Tuning Module
------------------
Prepares training data from sms_conversations.json and fine-tunes a model
for the Exit Advisor. The fine-tuned model learns to classify whether a
conversation should "end" or "continue" based on the conversation context.

Steps:
 1. Parse labeled conversations → extract training examples
 2. Format as OpenAI fine-tuning JSONL (chat completion format)
 3. Upload file to OpenAI
 4. Launch fine-tuning job
 5. Monitor until complete
"""

import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))
CONVERSATIONS_PATH = os.path.join(PROJECT_ROOT, "sms_conversations.json")
TRAINING_FILE = os.path.join(PROJECT_ROOT, "fine_tuning_data", "exit_advisor_training.jsonl")


def prepare_training_data() -> str:
    """
    Convert labeled conversations into fine-tuning examples.
    Each recruiter turn with a label becomes a training example where:
     - System prompt: Exit Advisor instructions
     - User message: conversation up to that point + candidate's latest message
     - Assistant response: "end" or "continue"

    Returns path to the JSONL file.
    """
    with open(CONVERSATIONS_PATH, "r", encoding="utf-8") as f:
        conversations = json.load(f)

    os.makedirs(os.path.dirname(TRAINING_FILE), exist_ok=True)
    examples = []

    system_msg = (
        "You are the Exit Advisor for a recruitment chatbot. "
        "Analyze the conversation and determine if it should end or continue. "
        "Respond with ONLY 'end' or 'continue'."
    )

    for conv in conversations:
        turns = conv["turns"]
        history_lines = []

        for i, turn in enumerate(turns):
            if turn["speaker"] == "recruiter" and turn.get("label"):
                label = turn["label"]
                # Map "schedule" → "continue" (scheduling is continuing)
                target = "end" if label == "end" else "continue"

                # Get the candidate message just before this recruiter turn
                candidate_msg = ""
                if i > 0 and turns[i - 1]["speaker"] == "candidate":
                    candidate_msg = turns[i - 1]["text"]

                history_text = "\n".join(history_lines) if history_lines else "(start of conversation)"

                example = {
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {
                            "role": "user",
                            "content": (
                                f"Conversation history:\n{history_text}\n\n"
                                f"Candidate's latest message:\n{candidate_msg}"
                            ),
                        },
                        {"role": "assistant", "content": target},
                    ]
                }
                examples.append(example)

            # Build up history
            speaker = turn["speaker"].capitalize()
            history_lines.append(f"{speaker}: {turn['text']}")

    with open(TRAINING_FILE, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"[Fine-Tuning] Created {len(examples)} training examples → {TRAINING_FILE}")
    return TRAINING_FILE


def upload_and_fine_tune(training_file: str | None = None) -> str:
    """
    Upload training file and start fine-tuning job.
    Returns the fine-tuning job ID.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    file_path = training_file or TRAINING_FILE

    # Upload
    with open(file_path, "rb") as f:
        upload_response = client.files.create(file=f, purpose="fine-tune")
    file_id = upload_response.id
    print(f"[Fine-Tuning] Uploaded file: {file_id}")

    # Start fine-tuning
    job = client.fine_tuning.jobs.create(
        training_file=file_id,
        model="gpt-4o-mini-2024-07-18",
        hyperparameters={"n_epochs": 3},
    )
    print(f"[Fine-Tuning] Job started: {job.id}")
    return job.id


def wait_for_fine_tuning(job_id: str) -> str:
    """
    Poll until job completes. Returns the fine-tuned model name.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    while True:
        job = client.fine_tuning.jobs.retrieve(job_id)
        status = job.status
        print(f"[Fine-Tuning] Status: {status}")

        if status == "succeeded":
            model_name = job.fine_tuned_model
            print(f"[Fine-Tuning] Done! Model: {model_name}")
            return model_name
        elif status in ("failed", "cancelled"):
            raise RuntimeError(f"Fine-tuning {status}: {job}")

        time.sleep(30)


def run_full_pipeline() -> str:
    """Convenience: prepare data → upload → fine-tune → wait → return model name."""
    training_file = prepare_training_data()
    job_id = upload_and_fine_tune(training_file)
    model_name = wait_for_fine_tuning(job_id)
    return model_name


# ── Run directly ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if "--prepare-only" in sys.argv:
        prepare_training_data()
    else:
        model = run_full_pipeline()
        print(f"\nFine-tuned model ready: {model}")
        print("Add this to your .env file:")
        print(f"FINE_TUNED_EXIT_MODEL={model}")
