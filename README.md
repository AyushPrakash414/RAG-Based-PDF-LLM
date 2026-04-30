# RAG-Based-PDF-LLM

A simple Retrieval-Augmented Generation (RAG) project built with:

- LangChain
- ChromaDB
- Hugging Face embeddings
- Gemini for final answer generation

This project reads local `.txt` files, splits them into chunks, stores embeddings in Chroma, and answers questions using retrieved context.

## Project Structure

```text
Rag-practice/
├── db/
│   └── chroma_db/            # persisted vector database
├── docunment/                # source text files
├── ingestion-pipeline.py     # loads docs, chunks text, creates embeddings
├── retrivalpipeline.py       # retrieves relevant chunks and asks Gemini
├── .gitignore
└── README.md
```

Note: the folder and file names currently use `docunment` and `retrivalpipeline.py`. The README keeps those names to match your existing code.

## How It Works

1. `ingestion-pipeline.py` loads `.txt` files from `docunment/`
2. The text is split into smaller chunks with overlap
3. Each chunk is converted into embeddings using `all-MiniLM-L6-v2`
4. Embeddings are stored in ChromaDB under `db/chroma_db`
5. `retrivalpipeline.py` retrieves the most relevant chunks for a question
6. Gemini uses that retrieved context to generate the final answer

## Requirements

- Python 3.10+
- A virtual environment
- `GOOGLE_API_KEY` in `.env`
- Internet access the first time the Hugging Face model is downloaded

## Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token
```

`HUGGINGFACEHUB_API_TOKEN` is optional but recommended because it helps avoid rate limits when downloading the embedding model.

## Install Dependencies

From the repository root:

```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

If you are not using the existing `venv`, create one first:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Step 1: Build the Vector Database

Run the ingestion pipeline:

```powershell
.\venv\Scripts\python Rag-practice\ingestion-pipeline.py
```

What this does:

- loads `.txt` files from `Rag-practice/docunment/`
- splits them into chunks with `RecursiveCharacterTextSplitter`
- creates embeddings with `HuggingFaceEmbeddings`
- stores the vectors in `Rag-practice/db/chroma_db`

## Step 2: Ask Questions

Run the retrieval pipeline:

```powershell
.\venv\Scripts\python Rag-practice\retrivalpipeline.py
```

Run it with a custom question:

```powershell
.\venv\Scripts\python Rag-practice\retrivalpipeline.py "What does the document say about Rama?"
```

## Example Flow

1. Put one or more `.txt` files inside `Rag-practice/docunment/`
2. Run `ingestion-pipeline.py`
3. Run `retrivalpipeline.py`
4. Ask questions based only on those documents

## Current Tech Choices

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector store: `Chroma`
- LLM: `gemini-3-flash-preview`
- Chunking: `RecursiveCharacterTextSplitter`

## Troubleshooting

### `GOOGLE_API_KEY is missing in the .env file`

Add your Gemini API key to the root `.env` file.

### `Vector database not found`

Run:

```powershell
.\venv\Scripts\python Rag-practice\ingestion-pipeline.py
```

before running the retrieval pipeline.

### Unicode or encoding errors

- Keep source `.txt` files in UTF-8 when possible
- The current loader already forces UTF-8 for text files
- The retrieval script reconfigures stdout for UTF-8 on Windows

### Hugging Face download warnings

The embedding model may need to download on first run. This is normal. Adding `HUGGINGFACEHUB_API_TOKEN` can make this smoother.

## Future Improvements

- support PDF and DOCX ingestion
- add source citations in answers
- build a Streamlit or Gradio UI
- expose chunk size and `k` as configurable arguments
- add automatic re-indexing when documents change

## Commands Summary

```powershell
.\venv\Scripts\python Rag-practice\ingestion-pipeline.py
.\venv\Scripts\python Rag-practice\retrivalpipeline.py
.\venv\Scripts\python Rag-practice\retrivalpipeline.py "Your question here"
```
