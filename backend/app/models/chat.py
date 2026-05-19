from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from ..database import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    user_query = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    products_referenced = Column(Text, nullable=True)
    was_helpful = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Clarification state for multi-turn disambiguation
    clarification_state = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ChatHistory(id={self.id}, query={self.user_query[:50]})>"
