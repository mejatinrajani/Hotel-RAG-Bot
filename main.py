import uuid
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from src.database import get_db, ChatSession, ChatMessage

app = FastAPI(title="Hotel Concierge RAG Microservice", version="1.0")

# Initialize orchestrator once on startup
orchestrator = None

# --- Pydantic Data Schemas ---
class SessionCreateResponse(BaseModel):
    session_id: str

class ChatRequest(BaseModel):
    session_id: str
    query: str

class MessageSchema(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    response: str
    intent: str
    status: str

class SessionListResponse(BaseModel):
    id: str
    title: str

class SessionCreateRequest(BaseModel):
    client_id: str

class FeedbackRequest(BaseModel):
    feedback: str # 'like' or 'dislike'

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "hotel-rag-backend"}

@app.get("/sessions", response_model=List[SessionListResponse])
def get_all_sessions(client_id: str, db: Session = Depends(get_db)):
    """Fetches only the sessions belonging to the requesting client_id"""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.client_id == client_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [{"id": str(s.id), "title": s.title} for s in sessions]

@app.post("/sessions", response_model=SessionCreateResponse)
def create_new_session(payload: SessionCreateRequest, db: Session = Depends(get_db)):
    """Generates a unique session UUID tied to a specific client_id"""
    new_session = ChatSession(client_id=payload.client_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return {"session_id": str(new_session.id)}

@app.get("/sessions/{session_id}/history")
def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    session = db.query(ChatSession).filter(ChatSession.id == session_uuid).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return [{"id": str(msg.id), "role": msg.role, "content": msg.content, "feedback": msg.feedback} for msg in session.messages]

@app.post("/chat")
def handle_chat_query(payload: ChatRequest, db: Session = Depends(get_db)):
    # --- LAZY LOADING FOR OCHESTRATOR ---
    global orchestrator
    if orchestrator is None:
        print("First request detected! Loading heavy RAG models into memory...")
        from src.rag_pipeline import HotelRAGOrchestrator
        orchestrator = HotelRAGOrchestrator(debug=True)

    session_uuid = uuid.UUID(payload.session_id)
    session = db.query(ChatSession).filter(ChatSession.id == session_uuid).first()
    
    recent_msgs = session.messages[-6:]
    history_list = [{"role": m.role, "content": m.content} for m in recent_msgs]

    # Update session title if it's the first message
    if session.title == "New Chat":
        session.title = payload.query[:40] + "..." if len(payload.query) > 40 else payload.query

    result = orchestrator.process_query(payload.query, history=history_list)
    ai_response_text = result["response"]

    user_msg = ChatMessage(session_id=session_uuid, role="user", content=payload.query)
    assistant_msg = ChatMessage(session_id=session_uuid, role="assistant", content=ai_response_text)
    
    db.add(user_msg)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg) # Refresh to get the generated message ID

    return {
        "message_id": str(assistant_msg.id), # Return ID so frontend can attach feedback to it
        "response": ai_response_text,
        "intent": result["intent"],
        "status": result["status"]
    }

@app.post("/messages/{message_id}/feedback")
def submit_feedback(message_id: str, payload: FeedbackRequest, db: Session = Depends(get_db)):
    """Updates the feedback column for a specific message"""
    msg_uuid = uuid.UUID(message_id)
    message = db.query(ChatMessage).filter(ChatMessage.id == msg_uuid).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.feedback = payload.feedback
    db.commit()
    return {"status": "success"}