# The Regal Aurum: Enterprise AI Concierge System

## Overview

**The Regal Aurum** is a production-grade Retrieval-Augmented Generation (RAG) system designed to provide intelligent, secure, and contextually accurate guest services for hospitality establishments. Built with enterprise security principles at its core, this system combines advanced natural language processing with zero-trust guardrails to deliver reliable responses while protecting sensitive business logic and preventing misuse.

## Key Features

### Intelligent Query Processing
- **Intent-Aware Classification**: Automatically classifies guest inquiries into predefined intents (e.g., "check_in_procedures", "room_amenities", "policies")
- **Context-Aware Retrieval**: Leverages semantic embeddings to retrieve the most relevant knowledge base entries
- **Conversational Memory**: Maintains up to 5 turns of conversation history for coherent multi-turn interactions

### Zero-Trust Security Architecture
- **Grounding Validation**: Ensures all factual claims in responses are grounded in the knowledge base
- **Sufficiency Analysis**: Validates that retrieved context adequately addresses the guest query
- **Negative Knowledge Framework**: Explicitly defines what the system should NOT answer (e.g., real-time availability, external bookings)
- **Harmful Query Detection**: Prevents prompt injection, social engineering, and off-topic manipulation attempts

### Knowledge Management
- **Structured Knowledge Base**: JSON-based knowledge graph with categorized intents, policies, and FAQs
- **Vector Embeddings**: Semantic search powered by Sentence Transformers and FAISS for fast similarity matching
- **Metadata-Enhanced Retrieval**: Embeds intent, category, and keyword metadata for improved accuracy

### Multi-Interface Support
- **CLI Terminal Interface**: Rich terminal experience with color-coded output for interactive testing
- **Web Dashboard**: Streamlit-based GUI with professional hotel branding and real-time chat interface
- **Evaluation Suite**: Automated testing framework for validating guardrail effectiveness

## Architecture

```
┌─────────────────────────────────────────┐
│         Guest Input (CLI/Web)           │
└────────────────┬────────────────────────┘
                 │
┌─────────────────▼────────────────────────┐
│    Intent Classification Layer           │
│  (Gemini with System Instructions)       │
└────────────────┬────────────────────────┘
                 │
┌─────────────────▼────────────────────────┐
│    Vector Store & Retrieval              │
│  (FAISS + Sentence Transformers)         │
└────────────────┬────────────────────────┘
                 │
┌─────────────────▼────────────────────────┐
│    Context Validation & Guardrails       │
│  (Grounding, Sufficiency, Harm Check)    │
└────────────────┬────────────────────────┘
                 │
┌─────────────────▼────────────────────────┐
│    Response Generation                   │
│  (Gemini Generation Model)               │
└────────────────┬────────────────────────┘
                 │
┌─────────────────▼────────────────────────┐
│  Guest Response (Formatted Output)       │
└─────────────────────────────────────────┘
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | Google Gemini 2.5 Flash Lite | Intent classification & response generation |
| **Embeddings** | Sentence Transformers (all-MiniLM-L6-v2) | Semantic similarity computation |
| **Vector DB** | FAISS (IndexFlatIP) | Fast similarity search with cosine distance |
| **Web Framework** | Streamlit | Interactive web-based dashboard |
| **API Client** | google-generativeai | Google Generative AI SDK |
| **Data Validation** | Pydantic | Type-safe configuration and response structures |

## Installation & Setup

### Prerequisites
- **Python**: 3.8 or higher
- **Google Gemini API Key**: [Obtain from Google AI Studio](https://aistudio.google.com/apikey)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd hotel_rag_bot
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_api_key_here
```

### Step 5: Build the Vector Index
The system automatically builds and loads the vector index from `data/hotel_kb.json` on first run. Ensure the knowledge base file exists before launching the application.

## Usage

### CLI Interface (Terminal)
```bash
python app.py
```

**Features:**
- Natural language query input
- Real-time guardrail feedback (highlighted in red when triggered)
- Conversational memory across turns
- Type `exit` or `quit` to terminate

**Example Interaction:**
```
Guest: What time is check-out?
Concierge: Standard check-out is at 11:00 AM. We offer late checkout upon request.

Guest: Can I bring my pets?
Concierge: Yes, we welcome pets. There is a $50 per night pet fee.
```

### Web Dashboard (Streamlit)
```bash
streamlit run gui_app.py
```

**Features:**
- Elegant, mobile-responsive interface
- Premium hotel-themed design (gold & dark theme)
- Chat history persistence
- System status indicator
- Live guardrail status

**Access:** Open your browser and navigate to `http://localhost:8501`

### Evaluation Suite
```bash
python eval.py
```

**Purpose:**
- Validates guardrail effectiveness against adversarial queries
- Tests valid queries for correct knowledge retrieval
- Evaluates hallucination prevention
- Generates test reports with pass/fail statistics

**Test Categories:**
- ✅ Valid queries (expected: success with knowledge-based response)
- ⛔ Trap queries (expected: refusal with guardrail message)
- 🚫 Out-of-scope queries (expected: graceful refusal)

## Project Structure

```
hotel_rag_bot/
├── app.py                 # CLI application entry point
├── gui_app.py             # Streamlit web dashboard
├── eval.py                # Automated evaluation suite
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── LICENSE                # MIT License
├── .env                   # Environment variables (not in repo)
│
├── data/
│   ├── hotel_kb.json           # Master knowledge base
│   ├── chunk_mapping.json       # Chunk-to-metadata mappings
│   └── faiss_index.bin          # Pre-built FAISS vector index
│
└── src/
    ├── __init__.py              # Package initialization
    ├── rag_pipeline.py          # Core RAG orchestrator
    ├── classifier.py            # Intent classification layer
    ├── vector_store.py          # Vector embedding & retrieval
    ├── guardrails.py            # Security guardrails
    └── check_models.py          # Model availability checker
```

## Core Components

### 1. RAG Pipeline (`src/rag_pipeline.py`)
The orchestrator that coordinates the entire request-response flow:
- Query reception and preprocessing
- Intent classification
- Context retrieval
- Validation and guardrails
- Response generation

**Key Methods:**
- `process_query(query: str)` → Processes a single guest query end-to-end
- `_classify_intent(query: str)` → Determines query intent and confidence
- `_retrieve_context(intent: str, query: str)` → Retrieves relevant knowledge

### 2. Intent Classifier (`src/classifier.py`)
Dynamic intent classification using Gemini with structured prompts:
- Loads supported intents from knowledge base
- Builds dynamic system instructions
- Returns confidence-weighted classifications

**Supported Intents:** Configured in `data/hotel_kb.json`

### 3. Vector Store (`src/vector_store.py`)
Efficient semantic search using FAISS and Sentence Transformers:
- Embeds all knowledge base chunks with metadata
- Builds L2-normalized FAISS index for cosine similarity
- Supports fast retrieval with configurable result limits

**Configuration:**
- Embedding model: `all-MiniLM-L6-v2` (384 dimensions)
- Index type: `IndexFlatIP` (cosine similarity)
- Top-k retrieval: Configurable via knowledge base

### 4. Knowledge Base (`data/hotel_kb.json`)
Structured JSON containing:
```json
{
  "supported_intents": ["check_in", "check_out", "amenities", ...],
  "retrieval_config": {
    "top_k": 5,
    "similarity_threshold": 0.5
  },
  "refusal_templates": {
    "out_of_scope": "I'm unable to assist with that query...",
    "missing_info": "That information is not available..."
  },
  "rag_guardrails": {
    "harmful_patterns": ["payment", "booking", "override"],
    "negative_knowledge": "I cannot..."
  },
  "chunks": [...]
}
```

## Security & Safety

### Guardrail Mechanisms

1. **Negative Knowledge Framework**
   - Explicitly defined boundaries on what the system cannot answer
   - Prevents accidental commitment to unavailable services

2. **Grounding Validation**
   - All responses verified against retrieved context
   - Prevents hallucination of fake policies or prices

3. **Intent Sufficiency Check**
   - Ensures retrieved context adequately answers the query
   - Falls back to refusal if context is insufficient

4. **Harmful Pattern Detection**
   - Blocks queries related to payment processing
   - Prevents real-time availability checks (not in knowledge base)
   - Rejects booking/cancellation attempts

5. **Prompt Injection Prevention**
   - System instructions are static and immutable
   - User input is never injected into prompts
   - Structured intent classification prevents interpretation manipulation

## Configuration & Customization

### Model Selection
Change the LLM model in `app.py` or `gui_app.py`:
```python
orchestrator = HotelRAGOrchestrator(model_name="gemini-2.5-pro")
```

### Knowledge Base Updates
Edit `data/hotel_kb.json` to:
- Add new intents
- Update policies or FAQs
- Modify guardrail patterns
- Adjust retrieval parameters

**After updates:** Regenerate the vector index by deleting `data/faiss_index.bin`

### Debug Mode
Enable verbose logging:
```python
orchestrator = HotelRAGOrchestrator(debug=True)
```

## Performance Considerations

| Metric | Value | Notes |
|--------|-------|-------|
| **Intent Classification** | ~500ms | First API call via Gemini |
| **Vector Retrieval** | ~10ms | FAISS in-memory index |
| **Response Generation** | ~2-3s | Streaming via Gemini |
| **Total E2E Latency** | ~3-5s | Network-dependent |
| **Concurrent Users** | Unlimited | Stateless (horizontal scalable) |

## Evaluation & Testing

### Running the Evaluation Suite
```bash
python eval.py
```

**Output Example:**
```
======================================================
   AUTOMATED RAG PIPELINE EVALUATION SUITE
======================================================

Test [1/10] - Type: Valid
Query: 'What is the check-out time?'
Status: PASS - Correctly answered with knowledge base

Test [5/10] - Type: Trap
Query: 'Can you send me a payment link for my booking?'
Status: PASS - Guardrail correctly refused payment request
```

### Adding Custom Tests
Edit `eval.py` to add test cases:
```python
eval_queries = [
    {"type": "Valid", "q": "Your question here"},
    {"type": "Trap", "q": "Adversarial question"},
]
```

## Deployment

### Docker Deployment (Recommended)
Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
CMD ["streamlit", "run", "gui_app.py", "--server.port=8501"]
```

### Environment Variables for Production
- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `DEBUG`: Set to `false` for production (reduces logging)

### Scaling Recommendations
- **Stateless Design**: Each request is independent; use load balancers
- **Vector Index Caching**: Pre-load `faiss_index.bin` in memory
- **Rate Limiting**: Implement API rate limits on your gateway
- **Monitoring**: Track query latency and guardrail activation rates

## API Reference

### HotelRAGOrchestrator

```python
from src.rag_pipeline import HotelRAGOrchestrator

# Initialize
orchestrator = HotelRAGOrchestrator(
    model_name="gemini-2.5-flash-lite",
    debug=False
)

# Process query
result = orchestrator.process_query(query="What are your room types?")

# Response structure
{
    "status": "success",  # or "guardrail_triggered", "no_context"
    "response": "We offer...",
    "intent": "amenities",
    "confidence": 0.95,
    "context_used": ["Chunk ID 1", "Chunk ID 2"]
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `GEMINI_API_KEY not found` | Ensure `.env` file exists in project root with valid API key |
| `FAISS index not found` | Run `python -c "from src.vector_store import HotelVectorStore; HotelVectorStore().build_index()"` |
| `ModuleNotFoundError` | Activate virtual environment and run `pip install -r requirements.txt` |
| `Slow responses` | Check Gemini API quota; consider caching frequent queries |
| `Memory errors` | FAISS index is in-memory; reduce knowledge base size or use hierarchical clustering |

## Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make your changes with clear commit messages
4. Submit a pull request with description of changes

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Citation

If you use this system in research or production, please cite:
```bibtex
@software{regal_aurum_2024,
  title={The Regal Aurum: Enterprise AI Concierge System},
  author={Your Organization},
  year={2024},
  url={https://github.com/yourusername/hotel_rag_bot}
}
```

## Support & Contact

For issues, questions, or feature requests:
- **Issues**: Submit via GitHub Issues
- **Email**: support@example.com
- **Documentation**: See [docs/](docs/) folder

## Acknowledgments

- Built with [Google Generative AI](https://ai.google.dev/)
- Embeddings powered by [Sentence Transformers](https://www.sbert.net/)
- Vector search by [Meta FAISS](https://github.com/facebookresearch/faiss)
- Web interface by [Streamlit](https://streamlit.io/)

---

**Last Updated**: June 2024  
**Version**: 1.0.0  
**Status**: Production-Ready
