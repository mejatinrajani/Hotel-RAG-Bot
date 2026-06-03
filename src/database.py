import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from dotenv import load_dotenv
load_dotenv()

# This will grab your Neon connection string from .env
DATABASE_URL = os.getenv("NEON_DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("CRITICAL ERROR: NEON_DATABASE_URL not found in .env")

# Initialize the SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
class ChatSession(Base):
    __tablename__ = "sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), default="New Chat")
    client_id = Column(String(255), default="default_user")  
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    feedback = Column(String(50), nullable=True) # NEW: 'like' or 'dislike'
    created_at = Column(DateTime, default=datetime.utcnow)
    session = relationship("ChatSession", back_populates="messages")

# Dependency function we will use in FastAPI to get a database connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()