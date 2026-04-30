import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()
if os.getenv("HUGGINGFACEHUB_API_TOKEN") and not os.getenv("HF_TOKEN"):
    os.environ["HF_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
PERSIST_DIRECTORY = BASE_DIR / "db" / "chroma_db"
COLLECTION_NAME = "rag_documents"
DEFAULT_QUERY = "Does the text prove that Rama historically existed?"


def get_embedding_model():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def load_vector_store():
    if not PERSIST_DIRECTORY.exists():
        raise FileNotFoundError(
            f"Vector database not found at {PERSIST_DIRECTORY}. Run ingestion-pipeline.py first."
        )

    return Chroma(
        persist_directory=str(PERSIST_DIRECTORY),
        embedding_function=get_embedding_model(),
        collection_name=COLLECTION_NAME,
    )


def retrieve_context(query, k=4):
    vector_store = load_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": k})
    documents = retriever.invoke(query)

    if not documents:
        return "", []

    context = "\n\n".join(doc.page_content for doc in documents)
    return context, documents


def ask_gemini(query, context):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY is missing in the .env file.")

    model = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        temperature=0.2,
    )

    prompt = f"""
Answer ONLY using the provided context.
Do not add interpretations or external knowledge.
If the answer is not clearly stated, say "Not explicitly mentioned".

Context:
{context}

Question:
{query}
"""

    response = model.invoke(prompt)
    if isinstance(response.content, list):
        text_blocks = [
            block.get("text", "")
            for block in response.content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(block for block in text_blocks if block).strip()

    return str(response.content).strip()


def main():
    query = " ".join(sys.argv[1:]).strip() or DEFAULT_QUERY
    context, documents = retrieve_context(query)

    if not documents:
        print("No relevant documents were found in the vector store.")
        return

    answer = ask_gemini(query, context)
    print("\nQuestion:")
    print(query)
    print("\nAnswer:")
    print(answer)


if __name__ == "__main__":
    main()
