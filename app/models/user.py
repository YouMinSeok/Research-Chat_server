from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.config import Base

class UserRole(str, enum.Enum):
    professor = "professor"
    assistant = "assistant"
    student = "student"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # hashed password
    role = Column(Enum(UserRole), nullable=False)
    profile_image = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    chat_room_members = relationship("ChatRoomMember", back_populates="user")
    project_memberships = relationship("ProjectMember", back_populates="user")
