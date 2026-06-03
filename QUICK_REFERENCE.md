# Hotel RAG Bot - Quick Reference Guide

## File Purpose Overview

### Root Directory Files

| File | Purpose | Key Info |
|------|---------|----------|
| `main.py` | CLI Terminal Interface | Run with `python main.py` for interactive testing |
| `app.py` | FastAPI Backend API | Run with `uvicorn app:app --reload` on port 8000 |
| `gui_app.py` | Streamlit Web Dashboard | Run with `streamlit run gui_app.py` on port 8501 |
| `eval.py` | Automated Testing Suite | Run with `python eval.py` to test guardrails |
| `requirements.txt` | Python Dependencies | Install with `pip install -r requirements.txt` |
| `.env` | Environment Configuration | Contains API keys and database URL |

### Data Directory

| File | Purpose | Contains |
|------|---------|----------|
| `hotel_kb.json` | Knowledge Base | All hotel information the AI knows |
| `faiss_index.bin` | Vector Index | Searchable embeddings (auto-generated) |
| `chunk_mapping.json` | Vector Mapping | Maps vectors to knowledge chunks (auto-generated) |

### Source Code Directory (src/)

| File | Class | Purpose |
|------|-------|---------|
| `rag_pipeline.py` | HotelRAGOrchestrator | Main orchestration logic for RAG |
| `classifier.py` | HotelIntentClassifier | Intent detection using Groq Llama |
| `vector_store.py` | HotelVectorStore | FAISS index management and search |
| `guardrails.py` | HotelGuardrails | Safety checks and validation |
| `database.py` | ChatSession, ChatMessage | Database models and session management |
| `__init__.py` | - | Python package marker |

---

## Quick Start Commands

### Local Development

```bash
# 1. Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Create .env file with:
# GROQ_API_KEY=your_key
# NEON_DATABASE_URL=sqlite:///./hotel_chat.db

# 3. Build vector index
python -c "from src.vector_store import HotelVectorStore; HotelVectorStore().build_index()"

# 4. Start backend (Terminal 1)
uvicorn app:app --reload --port 8000

# 5. Start frontend (Terminal 2)
streamlit run gui_app.py

# 6. Test CLI (Terminal 3, optional)
python main.py
```

### Testing

```bash
# Run evaluation suite
python eval.py

# Test specific endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "query": "What is checkout time?"}'
```

---

## Configuration Changes

### For Localhost Deployment

Change `gui_app.py` line ~14:

```python
# From:
API_BASE_URL = "https://hotel-rag-bot.onrender.com"

# To:
API_BASE_URL = "http://localhost:8000"
```

### For Production Deployment

Update `.env`:

```env
# Database
NEON_DATABASE_URL=postgresql://user:pass@host:5432/db

# API Keys (use production keys)
GROQ_API_KEY=prod_key
```

And `gui_app.py`:

```python
API_BASE_URL = "https://your-production-url.com"
```

---

## Core Concepts

### RAG Pipeline Flow

```
Query
  ↓
Intent Classification (What does user want?)
  ↓
Guardrail Check (Is it safe/allowed?)
  ↓
Vector Search (Find relevant knowledge)
  ↓
Context Validation (Is found info sufficient?)
  ↓
Response Generation (Create answer)
  ↓
Answer Validation (Is answer grounded?)
  ↓
Return Response
```

### Key Terms

| Term | Meaning | Example |
|------|---------|---------|
| Intent | What user wants | "pricing_query" for price questions |
| Retrieval | Finding relevant chunks | FAISS search returns top 5 matches |
| Context | Retrieved knowledge | Chunks about Premier Room pricing |
| Guardrail | Safety rule | Block "send payment link" requests |
| Grounding | Fact verification | Check answer is in retrieved context |
| Hallucination | Made-up information | AI inventing prices not in KB |
| Negative Knowledge | Out-of-scope answers | "Real-time availability not available" |

---

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| GROQ_API_KEY not found | .env missing or incorrect | Create .env with GROQ_API_KEY=your_key |
| Vector Store Index Not Found | Index not built | Run `python -c "from src.vector_store import HotelVectorStore; HotelVectorStore().build_index()"` |
| Connection refused on port 8000 | Backend not running | Start with `uvicorn app:app --reload` |
| Cannot connect to database | Wrong DATABASE_URL | Check NEON_DATABASE_URL in .env |
| API returned 404 | API_BASE_URL wrong in gui_app.py | Change to `http://localhost:8000` |
| ModuleNotFoundError | Dependencies not installed | Run `pip install -r requirements.txt` |

---

## Performance Optimization

### Cold Start (First Query)

Takes 30-60 seconds due to:
- Model downloads (~300MB)
- FAISS index loading
- Groq API connection

### Warm State (Subsequent Queries)

Takes 2-5 seconds:
- Models already in memory
- Just calling Groq API
- Vector search is fast

### Optimization Tips

1. **Run backend continuously** - Keeps models in memory
2. **Use GPU for embeddings** - Edit `vector_store.py` if available
3. **Cache FAISS index** - Already done, just load from disk
4. **Pre-warm with dummy query** - On startup, send test query

---

## Database Schema

### ChatSession

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    title VARCHAR(255),
    client_id VARCHAR(255),
    created_at TIMESTAMP,
    FOREIGN KEY (messages)
);
```

### ChatMessage

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    session_id UUID FOREIGN KEY,
    role VARCHAR(50),  -- "user" or "assistant"
    content TEXT,
    feedback VARCHAR(50),  -- "like" or "dislike"
    created_at TIMESTAMP
);
```

---

## API Response Examples

### Successful Response

```json
{
  "response": "The Premier Room costs $250 per night and includes breakfast and Wi-Fi.",
  "intent": "pricing_query",
  "status": "success",
  "chunks_retrieved": 3
}
```

### Refused Response

```json
{
  "response": "I cannot check real-time availability. Please contact the front desk.",
  "intent": "real_time_availability",
  "status": "refused_negative_knowledge",
  "chunks_retrieved": 1
}
```

### Insufficient Information

```json
{
  "response": "I don't have that information in my knowledge base.",
  "intent": "general_information",
  "status": "refused_insufficient_context",
  "chunks_retrieved": 0
}
```

---

## Knowledge Base Structure

### Retrieval Chunk Format

```json
{
  "id": "chunk_001",
  "intent": "pricing_query",
  "category": "pricing",
  "keywords": ["premier", "room", "price"],
  "text": "The Premier Room costs $250 per night...",
  "source_section": "Room Pricing"
}
```

### Negative Knowledge Format

```json
{
  "id": "neg_001",
  "category": "unsupported_information",
  "intent": "booking",
  "text": "I cannot create bookings. Contact the front desk...",
  "reason": "Requires payment processing"
}
```

---

## Environment Variables

### Required

```env
GROQ_API_KEY=gsk_xxxxx  # Get from Groq console
NEON_DATABASE_URL=...    # PostgreSQL or SQLite connection
```

### Optional

```env
DEBUG=true              # Enable debug logging
LOG_LEVEL=INFO         # Logging level
```

### For Production

```env
NEON_DATABASE_URL=postgresql://user:pass@prod-db:5432/hotel_rag
GROQ_API_KEY=gsk_prod_key
```

---

## Deployment Checklist

- [ ] All dependencies in requirements.txt
- [ ] .env file with production API keys
- [ ] Database URL points to production DB
- [ ] Vector index built and included
- [ ] Knowledge base (hotel_kb.json) updated
- [ ] API_BASE_URL updated in gui_app.py
- [ ] Tested all three interfaces locally
- [ ] Evaluation suite passes (eval.py)
- [ ] HTTPS enabled on production
- [ ] Database backups configured
- [ ] Error logging configured
- [ ] User feedback collection working

---

## Monitoring and Maintenance

### Check System Health

```bash
# API health
curl http://localhost:8000/health

# Backend logs
uvicorn app:app --reload --log-level debug

# Database connection
python -c "from src.database import SessionLocal; db = SessionLocal(); print('DB OK')"

# Vector store
python -c "from src.vector_store import HotelVectorStore; store = HotelVectorStore(); store.load_index(); print('Index OK')"
```

### Common Maintenance Tasks

1. **Update Knowledge Base**
   - Edit `data/hotel_kb.json`
   - Rebuild index: `python -c "from src.vector_store import HotelVectorStore; HotelVectorStore().build_index()"`
   - Restart backend

2. **Review Feedback**
   - Query messages with feedback from database
   - Use feedback to improve knowledge base

3. **Monitor API Performance**
   - Track response times
   - Monitor error rates
   - Check vector search quality

4. **Database Cleanup**
   - Archive old sessions periodically
   - Delete feedback older than 90 days (or your retention policy)

---

## Development Workflow

### Making Changes

1. **Edit code** (e.g., `src/classifier.py`)
2. **For dynamic content:** Restart FastAPI (`Ctrl+C` then rerun)
3. **For GUI changes:** Streamlit auto-reloads
4. **For KB changes:** Rebuild vector index
5. **Test with eval.py:** `python eval.py`

### Adding New Intent

1. Add to `supported_intents` in `hotel_kb.json`
2. Add example in classifier system prompt
3. Add relevant chunks to `retrieval_chunks`
4. Rebuild vector index
5. Test with `python main.py`

### Adding New Feature

1. Determine which file to modify
2. Write code following existing patterns
3. Add tests in `eval.py` if applicable
4. Test manually with CLI
5. Test with Streamlit GUI
6. Test via curl

---

## File Structure Overview

```
hotel_rag_bot/
│
├── main.py                    ← CLI interface
├── app.py                     ← FastAPI backend
├── gui_app.py                 ← Streamlit web
├── eval.py                    ← Test suite
├── requirements.txt           ← Dependencies
├── .env                       ← Configuration (CREATE THIS)
│
├── data/
│   ├── hotel_kb.json         ← Knowledge base
│   ├── faiss_index.bin       ← Vector index (auto-created)
│   └── chunk_mapping.json    ← Vector mapping (auto-created)
│
├── src/
│   ├── rag_pipeline.py       ← Main orchestrator
│   ├── classifier.py         ← Intent classifier
│   ├── vector_store.py       ← FAISS search
│   ├── guardrails.py         ← Safety checks
│   ├── database.py           ← DB models
│   └── __init__.py           ← Python package
│
└── Documentation/
    ├── LOCALHOST_SETUP_GUIDE.md       ← How to run locally
    ├── PROJECT_ARCHITECTURE.md        ← Technical details
    └── README.md                      ← Original overview
```

---

## Glossary

- **RAG:** Retrieval-Augmented Generation - Answer generation using retrieved facts
- **Intent:** What the user wants to do
- **Embedding:** Vector representation of text meaning
- **FAISS:** Fast similarity search index
- **Guardrail:** Safety rule or validation check
- **Grounding:** Ensuring answers are based on source information
- **Hallucination:** AI making up false information
- **Chunking:** Breaking knowledge base into searchable pieces
- **Cold Start:** First query with models not in memory
- **Warm State:** Subsequent queries with models cached

---

## Getting Help

### Debugging Steps

1. Check `.env` file exists with correct API keys
2. Run `curl http://localhost:8000/health` - is backend running?
3. Check logs in terminal where FastAPI is running
4. Run `python eval.py` - do guardrails work?
5. Check `hotel_kb.json` - is it valid JSON?
6. Run `python main.py` - does CLI work?

### Common Questions

**Q: Why is the first query so slow?**
A: Models are loaded for the first time. Subsequent queries are fast.

**Q: Can I use a different LLM?**
A: Edit `rag_pipeline.py` to use Google Gemini or other APIs.

**Q: How do I update hotel information?**
A: Edit `data/hotel_kb.json` and rebuild the vector index.

**Q: Can multiple users use it simultaneously?**
A: Web dashboard (Streamlit) is single-user. FastAPI backend supports multiple users.

**Q: What if the AI hallucinates?**
A: This is prevented by grounding validation. If it happens, the knowledge base might be missing information.
