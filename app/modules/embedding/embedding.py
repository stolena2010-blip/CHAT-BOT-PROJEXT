"""
Embedding Module
-----------------
Reads the Python Developer Job Description PDF, splits it into chunks,
creates vector embeddings via OpenAI, and stores them in a local ChromaDB.
This is an offline/one-time step — the resulting DB is used at runtime
by the Info Advisor to answer candidate questions about the position.
"""

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))
PDF_PATH = os.path.join(PROJECT_ROOT, "Python Developer Job Description.pdf")
CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_db")
COLLECTION_NAME = "job_description"


def build_vector_store() -> Chroma:
    """Load PDF ➜ split ➜ embed ➜ persist in ChromaDB. Returns the vector store."""
    # 1. Load PDF pages
    loader = PyPDFLoader(PDF_PATH)
    pages = loader.load()
    print(f"[Embedding] Loaded {len(pages)} page(s) from PDF")

    # 2. Split into chunks (overlap keeps context across boundaries)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(pages)
    print(f"[Embedding] Split into {len(chunks)} chunks")

    # 3. Create embeddings & persist
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME,
    )
    print(f"[Embedding] Stored {len(chunks)} vectors in {CHROMA_DIR}")
    return vector_store


def get_vector_store() -> Chroma:
    """Return an existing ChromaDB vector store (call build_vector_store first)."""
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )


# ── Run directly to build the DB ──────────────────────────────────────
if __name__ == "__main__":
    build_vector_store()
    print("[Embedding] Done.")
