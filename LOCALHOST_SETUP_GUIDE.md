# Running Hotel RAG Bot on Localhost

## Quick Summary

The Hotel RAG Bot is currently deployed on Render.com with a hosted PostgreSQL database. To run it locally on your machine, you need to change the API configuration from a remote URL to `localhost:8000` and set up a local database.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL installed locally (or SQLite as alternative)
- Google Gemini API Key or Groq API Key
- 4GB+ RAM for LLM model loading
- Internet connection for downloading ML models

## Step-by-Step Installation

### Step 1: Clone and Setup Environment

```bash
cd hotel_rag_bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Create a `.env` file in the project root directory with the following variables:

```env
# API Keys (use ONE of these)
GROQ_API_KEY=your_groq_api_key_here
# OR
GEMINI_API_KEY=your_gemini_api_key_here

# For Local Deployment: Switch Database URL
# Option 1: Use SQLite (easiest for local development)
NEON_DATABASE_URL=sqlite:///./hotel_chat.db

# Option 2: Use Local PostgreSQL
# NEON_DATABASE_URL=postgresql://user:password@localhost:5432/hotel_rag_bot
```

### Step 3: Modify API Configuration

**This is the main change for localhost deployment.**

Edit `gui_app.py` and change this line:

```python
# BEFORE (Deployed Version):
API_BASE_URL = "https://hotel-rag-bot.onrender.com"

# AFTER (Localhost):
API_BASE_URL = "http://localhost:8000"
```

### Step 4: Build the Vector Store Index

Before running the application, build the FAISS vector index locally:

```bash
python -c "from src.vector_store import HotelVectorStore; store = HotelVectorStore(); store.build_index()"
```

This creates:
- `data/faiss_index.bin` - The vector search index
- `data/chunk_mapping.json` - Mapping of vectors to knowledge chunks

### Step 5: Start the Backend API Server

Open Terminal 1 and run:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 6: Start the Web Dashboard (Streamlit)

Open Terminal 2 in the project root and run:

```bash
streamlit run gui_app.py
```

Streamlit will open in your default browser at `http://localhost:8501`

### Step 7: Test the CLI Interface (Optional)

Open Terminal 3 to test the CLI:

```bash
python main.py
```

Type your first question and press Enter. You should see the AI response with color-coded output.

## What Changed for Localhost

### 1. API Base URL

**File:** `gui_app.py` (Line ~14)

```python
# Changed from remote URL to local
API_BASE_URL = "http://localhost:8000"
```

### 2. Database Configuration

**File:** `.env` file

For SQLite (recommended for local testing):
```env
NEON_DATABASE_URL=sqlite:///./hotel_chat.db
```

For PostgreSQL, ensure PostgreSQL is running:
```env
NEON_DATABASE_URL=postgresql://user:password@localhost:5432/hotel_rag_bot
```

### 3. Vector Index Location

The vector store files are saved in `data/` directory locally:
- `data/faiss_index.bin`
- `data/chunk_mapping.json`

These are automatically created when you run the build command.

## Architecture When Running Locally

```
┌─────────────────────────────────────────┐
│    Web Browser (Port 8501)              │
│  Streamlit GUI: gui_app.py              │
└──────────────┬──────────────────────────┘
               │ HTTP Requests
               ▼
┌─────────────────────────────────────────┐
│  FastAPI Backend (Port 8000)            │
│  File: app.py                           │
│  - Chat endpoint                        │
│  - Session management                   │
│  - Feedback collection                  │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┬──────────┐
    ▼                     ▼          ▼
┌─────────────┐  ┌──────────────┐  ┌────────┐
│ RAG Pipeline│  │ Local SQLite/ │  │ Vector │
│ (Groq LLM)  │  │ PostgreSQL    │  │ Store  │
│ classifier  │  │ Database      │  │ (FAISS)│
│ guardrails  │  │ (Sessions)    │  │        │
└─────────────┘  └──────────────┘  └────────┘
```

## Running Different Interfaces

### Option 1: Web Dashboard (Recommended for Users)
```bash
streamlit run gui_app.py
# Access at http://localhost:8501
```

### Option 2: CLI Terminal Interface (For Testing)
```bash
python main.py
# Type questions directly in terminal
# Color-coded output for guardrails
```

### Option 3: Direct API Access
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "query": "What is the check-out time?"
  }'
```

## API Endpoints Available Locally

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check if API is running |
| `/sessions` | GET | Fetch user chat sessions |
| `/sessions` | POST | Create new chat session |
| `/sessions/{session_id}/history` | GET | Get chat history |
| `/chat` | POST | Send query and get response |
| `/messages/{message_id}/feedback` | POST | Submit feedback (like/dislike) |

## Troubleshooting

### Error: GROQ_API_KEY not found

**Solution:** Ensure your `.env` file is in the root directory and contains:
```env
GROQ_API_KEY=your_actual_key_here
```

### Error: Vector Store Index Not Found

**Solution:** Run the build command:
```bash
python -c "from src.vector_store import HotelVectorStore; store = HotelVectorStore(); store.build_index()"
```

### Error: Connection refused on port 8000

**Solution:** 
1. Ensure FastAPI backend is running in another terminal
2. Check if port 8000 is already in use: `netstat -tulpn | grep 8000`
3. If in use, kill the process or use a different port

### Error: "Cannot connect to database"

**Solution:**
1. If using SQLite: Ensure `.env` has `NEON_DATABASE_URL=sqlite:///./hotel_chat.db`
2. If using PostgreSQL: Verify PostgreSQL is running and credentials are correct
3. Check that the directory has write permissions

### Streamlit Error: "API returned 404"

**Solution:**
1. Verify `API_BASE_URL` is correct in `gui_app.py`
2. Ensure FastAPI backend is running and healthy
3. Test backend directly: `curl http://localhost:8000/health`

## Performance Considerations

- **First Startup:** Takes 30-60 seconds as ML models are downloaded and loaded
- **Subsequent Startups:** 5-10 seconds (models cached)
- **Query Response Time:** 3-5 seconds (depends on internet for Groq API calls)
- **Memory Usage:** ~2-3GB when running all components

## Deployment Back to Cloud

To deploy back to Render.com or another cloud service:

1. Revert `gui_app.py` to use remote URL
2. Update `.env` with cloud database URL
3. Push to GitHub and configure deployment

Example for Render:
```python
API_BASE_URL = "https://your-app-name.onrender.com"
```

## File Structure for Local Deployment

```
hotel_rag_bot/
├── .env (NEW - contains local config)
├── app.py (FastAPI backend)
├── gui_app.py (Streamlit frontend - modified)
├── main.py (CLI interface)
├── requirements.txt
├── data/
│   ├── hotel_kb.json
│   ├── faiss_index.bin (generated locally)
│   └── chunk_mapping.json (generated locally)
├── src/
│   ├── rag_pipeline.py
│   ├── classifier.py
│   ├── vector_store.py
│   ├── guardrails.py
│   ├── database.py
│   └── __init__.py
└── hotel_chat.db (SQLite database - auto-created)
```

## Summary of Changes

| Component | Deployed | Localhost |
|-----------|----------|-----------|
| API URL | Render.com | localhost:8000 |
| Database | Neon PostgreSQL | SQLite or local PostgreSQL |
| Backend Port | 80/443 | 8000 |
| Frontend Port | 443 | 8501 (Streamlit) |
| API Key | Render environment | .env file |
| Vector Index | Built at runtime | Built locally on demand |

## Next Steps

1. Follow the Step-by-Step Installation above
2. Start with the Web Dashboard for testing
3. Use CLI for debugging guardrails
4. Check the logs for any errors
5. Test with sample queries from the eval.py file

For more technical details about how the system works, see `PROJECT_ARCHITECTURE.md`.
