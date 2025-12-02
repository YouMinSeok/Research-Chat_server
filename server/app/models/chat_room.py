from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config import Base

class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, nullable=False)  # 'project' or 'dm'

    # For project chat rooms
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)

    # For DM chat rooms
    user1_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    user2_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="chat_rooms")
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    members = relationship("ChatRoomMember", back_populates="chat_room", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="chat_room", cascade="all, delete-orphan")
    versions = relationship("ChatVersion", back_populates="chat_room", cascade="all, delete-orphan")

class ChatRoomMember(Base):
    __tablename__ = "chat_room_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chat_room_id = Column(String, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chat_room = relationship("ChatRoom", back_populates="members")
    user = relationship("User", back_populates="chat_room_members")
