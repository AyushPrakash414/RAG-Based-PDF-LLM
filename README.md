# Self-Healing RAG Microservice

A production-ready, **Self-Healing Retrieval-Augmented Generation (RAG)** microservice built with Python, FastAPI, Groq, and Qdrant.

## Architecture Overview

```
User Question
     │
     ▼
┌─────────────┐
│  FastAPI     │  POST /ask
│  API Layer   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│                  Orchestrator Service                     │
│                                                          │
│  Attempt 1: Retrieve(k=4)  → Validate → Generate → Critic│
│  Attempt 2: Rewrite → Retrieve(k=8)  → Validate → ...   │
│  Attempt 3: Rewrite → Retrieve(k=12) → Validate → ...   │
│  Fallback:  "Insufficient information"                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────┐   ┌──────────────┐   ┌─────────────────┐
│  Qdrant     │   │  Groq LLM    │   │  Trace Storage  │
│  Vector DB  │   │  Provider    │   │  (JSON files)   │
└─────────────┘   └──────────────┘   └─────────────────┘
```

## Key Features

- **Self-Healing Pipeline**: 3-stage retry with escalating retrieval strategies
- **Retrieval Validation**: Validates chunk relevance before generation
- **Answer Grounding**: Critic evaluates if answers are grounded in context
- **Query Rewriting**: Automatically rewrites queries for better retrieval
- **Full Tracing**: Every request produces a detailed JSON trace
- **LLM Abstraction**: Swap Groq for OpenAI/Claude without changing services
- **Vector Store Abstraction**: Swap Qdrant for Pinecone/Weaviate/ChromaDB
- **Async Support**: Built for concurrent users with async/await
- **Source Citations**: Every answer includes source documents

## Project Structure

```
├── app/
│   ├── api/
│   │   └── routes.py              # FastAPI endpoints
│   ├── services/
│   │   ├── retrieval_service.py   # Vector store search
│   │   ├── retrieval_validator.py # Chunk relevance validation
│   │   ├── answer_generator.py    # LLM answer generation
│   │   ├── answer_critic.py       # Answer grounding evaluation
│   │   ├── query_rewriter.py      # Query optimization
│   │   └── orchestrator_service.py# Self-healing orchestration
│   ├── interfaces/
│   │   ├── llm_provider.py        # Abstract LLM interface
│   │   └── vector_store.py        # Abstract vector store interface
│   ├── providers/
│   │   ├── groq_provider.py       # Groq implementation
│   │   └── qdrant_vector_store.py # Qdrant implementation
│   ├── prompts/                   # Prompt templates (TXT)
│   ├── models/                    # Pydantic models
│   ├── config/
│   │   └── settings.py            # Environment configuration
│   ├── utils/
│   │   └── logger.py              # Structured logging
│   └── main.py                    # FastAPI app entry point
├── scripts/
│   └── ingest_documents.py        # Document ingestion script
├── documents/                     # Source TXT documents
├── traces/                        # Execution trace JSON files
├── tests/
├── requirements.txt
├── .env
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for Qdrant) or Qdrant Cloud account
- Groq API key

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Qdrant (Local Docker)

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 3. Configure Environment

Edit `.env` with your credentials:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
QDRANT_URL=http://localhost:6333
```

### 4. Ingest Documents

Place your `.txt` files in the `documents/` directory, then run:

```bash
python scripts/ingest_documents.py
```

### 5. Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Test the API

```bash
# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Does the text prove that Rama historically existed?"}'

# Health check
curl -X POST http://localhost:8000/health
```

## API Endpoints

### POST /ask

**Request:**
```json
{
  "question": "Does the text prove that Rama historically existed?"
}
```

**Response:**
```json
{
  "answer": "Based on the provided context...",
  "sources": ["ram.txt"],
  "confidence": 0.91,
  "retrieval_confidence": 0.88,
  "attempts": 1,
  "status": "APPROVED"
}
```

### POST /health

**Response:**
```json
{
  "api": "UP",
  "groq": "UP",
  "qdrant": "UP"
}
```

## Self-Healing Strategy

| Attempt | Strategy     | Top-K | Threshold | Query Rewrite |
|---------|-------------|-------|-----------|---------------|
| 1       | Default     | 4     | 0.30      | No            |
| 2       | Expanded    | 8     | 0.30      | Yes           |
| 3       | Aggressive  | 12    | 0.20      | Yes           |

## Future Integration

Designed for integration into a microservices architecture:

```
React Frontend → Spring Boot API Gateway → Self-Healing RAG (FastAPI) → Qdrant + Groq
```

## License

MIT
