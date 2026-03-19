# 🔥 Hell Corp — SMS Recruitment Chatbot

A multi-agent AI chatbot that conducts SMS conversations with job candidates for a **Python Developer** position at **Hell Corp's 7th Circle Branch**. The bot gathers information, answers questions, and schedules interviews — all autonomously, with a devilish sense of humor.

## Project Purpose

Automate the initial recruitment screening process using a system of specialized AI agents:
- **Main Agent** — orchestrates the conversation, screens candidates (experience, frameworks, teamwork, projects, motivation), and decides the next action
- **Info Advisor** — answers candidate questions using RAG (job description in ChromaDB)
- **Scheduling Advisor** — finds available interview slots via SQL database (function calling), confirms before booking
- **Exit Advisor** — detects when a candidate is disinterested (fine-tuned model)

### Personal Touch 😈
- When an interview is booked → **"Welcome to Hell 🔥"**
- When the candidate is not interested → **"Maybe you'll have better luck in Paradise 😇"**

## Models Used

| Component | Model | Purpose |
|-----------|-------|---------|
| Main Agent | `gpt-4o` | Conversation orchestration, action classification |
| Info Advisor | `gpt-4o` | RAG-based Q&A about the job position |
| Scheduling Advisor | `gpt-4o` | Function calling for interview scheduling |
| Exit Advisor (base) | `gpt-4o` | Fallback conversation-end detection |
| Exit Advisor (fine-tuned) | `ft:gpt-4o-mini-2024-07-18:personal::DKjrJXBp` | Fine-tuned end/continue classifier |
| Embeddings | `text-embedding-3-small` | Document vectorization for ChromaDB |

## How to Install and Run

### Prerequisites
- Python 3.11+
- OpenAI API key

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd project

# 2. Create virtual environment
python -m venv .venv

# 3. Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment variables
# Edit .env and set your OPENAI_API_KEY
```

### Build the Vector Store (one-time setup)

```bash
python -m app.modules.embedding.embedding
```

### Fine-Tune the Exit Advisor (optional)

```bash
# Prepare training data only:
python -m app.modules.fine_tuning.fine_tuning --prepare-only

# Full pipeline (prepare + upload + fine-tune):
python -m app.modules.fine_tuning.fine_tuning
# When done, add FINE_TUNED_EXIT_MODEL=ft:... to your .env
```

### Run the Chatbot

#### CLI Mode
```bash
python -m app.main
```

#### Streamlit Web UI
```bash
streamlit run streamlit_app/streamlit_main.py
```

### Run Evaluation
```bash
python -m app.modules.evaluation.evaluation
```
Or open `tests/test_evals.ipynb` in Jupyter.

## Evaluation Results

**Accuracy: 88.14%** with GPT-4o on 59 labeled examples (15 conversations).

| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|--------|
| continue | 0.91 | 0.80 | 0.85 | 25 |
| schedule | 0.77 | 0.89 | 0.83 | 19 |
| end | 1.00 | 1.00 | 1.00 | 15 |

### Model Comparison Experiments

| Model | Type | Accuracy | Notes |
|-------|------|----------|-------|
| **GPT-4o** | General | **88.14%** | Best — fast, focused, accurate |
| o4-mini | Reasoning (small) | 71.19% | Over-reasons simple classifications |
| GPT-5.4 | General (new) | 62-68% | Not calibrated for existing prompts |

## Basic Usage Examples

**CLI interaction:**
```
Recruiter: Hi, thanks for submitting your application...
Candidate: I have 5 years of Python experience with Django.
Recruiter: Great! Could we schedule an interview? We have slots on...
  [action: schedule]
```

**Streamlit:** Open the web UI, type messages as a candidate, and watch the bot respond with appropriate actions.

## Project Structure

```
|-- .gitignore                              # Git ignore rules
|-- .env                                    # API keys (not in git)
|-- README.md                               # This file
|-- requirements.txt                        # Python dependencies
|-- sms_conversations.json                  # Labeled test dataset (15 conversations)
|-- db_Tech.sql                             # SQL schema for schedule table
|-- Python Developer Job Description.pdf    # Source for embeddings
|
|-- app/                                    # Main application code
|   |-- __init__.py
|   |-- main.py                             # CLI entry point
|   |-- modules/
|       |-- __init__.py
|       |-- agents/                         # AI Agents
|       |   |-- __init__.py
|       |   |-- main_agent.py               # Orchestrator (Main Agent)
|       |   |-- info_advisor.py             # RAG-based Q&A advisor
|       |   |-- scheduling_advisor.py       # Function-calling scheduler
|       |   |-- exit_advisor.py             # End-of-conversation detector
|       |-- database/                       # SQL Database module
|       |   |-- __init__.py
|       |   |-- database.py                 # Schedule queries
|       |-- embedding/                      # ChromaDB embedding module
|       |   |-- __init__.py
|       |   |-- embedding.py                # PDF → vectors
|       |-- fine_tuning/                    # Fine-tuning module
|       |   |-- __init__.py
|       |   |-- fine_tuning.py              # Training data prep + job launch
|       |-- evaluation/                     # Evaluation module
|           |-- __init__.py
|           |-- evaluation.py               # Accuracy + confusion matrix
|
|-- streamlit_app/                          # Streamlit web UI
|   |-- __init__.py
|   |-- streamlit_main.py                   # Chat interface
|   |-- utils.py                            # Helper functions
|
|-- tests/                                  # Tests & evaluation
|   |-- test_evals.ipynb                    # Jupyter notebook with metrics
```
