from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.message import MessageType

# ChatRoom Schemas
class ChatRoomCreate(BaseModel):
    name: str
    description: Optional[str] = None
    member_ids: List[str]

class ChatRoomResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatRoomWithMembers(ChatRoomResponse):
    member_ids: List[str]

# Message Schemas
class MessageCreate(BaseModel):
    chat_room_id: str
    type: MessageType
    content: str
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    parent_message_id: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    chat_room_id: str
    sender_id: str
    sender_name: str
    sender_role: str
    type: MessageType
    content: str
    timestamp: datetime
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    parent_message_id: Optional[str] = None
    feedback_ids: List[str] = []

    class Config:
        from_attributes = True

# Version Schemas
class VersionCreate(BaseModel):
    chat_room_id: str
    description: Optional[str] = None

class VersionResponse(BaseModel):
    id: str
    chat_room_id: str
    version_number: int
    description: Optional[str] = None
    created_at: datetime
    created_by: str
    message_ids: List[str] = []

    class Config:
        from_attributes = True
