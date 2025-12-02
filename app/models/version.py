from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config import Base

class ChatVersion(Base):
    __tablename__ = "chat_versions"

    id = Column(String, primary_key=True, index=True)
    chat_room_id = Column(String, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=False)  # user_id who created this version

    # 메시지 ID들을 JSON 배열로 저장
    message_ids = Column(JSON, default=list)

    # Relationships
    chat_room = relationship("ChatRoom", back_populates="versions")
