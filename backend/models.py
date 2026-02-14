from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# 1. The User Table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # In production, this should be hashed!
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship: One User has many Chat Messages
    # cascade="all, delete" means if you delete the User, their chats are also deleted.
    chats = relationship("ChatHistory", back_populates="owner", cascade="all, delete-orphan")

# 2. The Chat History Table
class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True, nullable=False)  # Groups messages into a "Session"
    role = Column(String, nullable=False)     # "user" or "assistant"
    content = Column(Text, nullable=False)    # The actual message text
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign Key: Links this message to a specific User ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationship link back to User
    owner = relationship("User", back_populates="chats")

# Note: The 'documents' table (for vectors) is handled separately by LangChain,
# so we don't need to define it here for now.