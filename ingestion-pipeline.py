import os
from pathlib import Path
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()
if os.getenv("HUGGINGFACEHUB_API_TOKEN") and not os.getenv("HF_TOKEN"):
    os.environ["HF_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_DIR = BASE_DIR / "db" / "chroma_db"
COLLECTION_NAME = "rag_documents"


def load_Docunment(doc_path="docunment"):
    full_doc_path = BASE_DIR / doc_path
    if not full_doc_path.exists():
        raise FileNotFoundError("file not found")
    loader = DirectoryLoader(
        path=str(full_doc_path),
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docunment = loader.load()
    return docunment


def main():
    #Loding the data
    print("main function is working")
    text = load_Docunment("docunment")
    #chunking the doc
    chunks = chunking(text)
    create_vector_store(chunks)
    

def chunking(docunment, chunk_size=800, chunk_overlap=100):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = text_splitter.split_documents(docunment)
    print(f"Created {len(chunks)} chunks")
    return chunks

def create_vector_store(chunks, persist_directory=DEFAULT_DB_DIR):
    print("Creating embeddings and storing in ChromaDB ... ")

    embedding_model = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    print(" --- Creating vector store --- ")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=str(persist_directory),
        collection_name=COLLECTION_NAME,
        collection_metadata={"hnsw:space": "cosine"}
    )

    print(" --- Finished creating vector store --- ")
    print(f"Vector store created and saved to {persist_directory}")

    return vectorstore

main()
