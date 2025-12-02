from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.config import Base

class MessageType(str, enum.Enum):
    text = "text"
    file = "file"
    feedback = "feedback"
    system = "system"

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    chat_room_id = Column(String, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sender_name = Column(String, nullable=False)
    sender_role = Column(String, nullable=False)  # professor, assistant, student
    type = Column(Enum(MessageType), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # 파일 관련
    file_url = Column(String, nullable=True)
    file_name = Column(String, nullable=True)

    # 피드백 관련
    parent_message_id = Column(String, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    feedback_ids = Column(JSON, default=list)  # 이 메시지에 달린 피드백 ID 리스트

    # Relationships
    chat_room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User", back_populates="messages", foreign_keys=[sender_id])
    parent_message = relationship("Message", remote_side=[id], foreign_keys=[parent_message_id])
