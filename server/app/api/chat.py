from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
from datetime import datetime
from app.config import get_db
from app.models.user import User
from app.models.chat_room import ChatRoom, ChatRoomMember
from app.models.message import Message
from app.models.version import ChatVersion
from app.schemas.chat import (
    ChatRoomCreate,
    ChatRoomResponse,
    ChatRoomWithMembers,
    MessageCreate,
    MessageResponse,
    VersionCreate,
    VersionResponse,
)
from app.auth import get_current_user

router = APIRouter(prefix="/api/chat", tags=["chat"])

# ========== Chat Room APIs ==========

@router.post("/rooms", response_model=ChatRoomWithMembers)
def create_chat_room(
    room_data: ChatRoomCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 채팅방 생성
    chat_room = ChatRoom(
        id=str(uuid4()),
        name=room_data.name,
        description=room_data.description,
    )
    db.add(chat_room)
    db.flush()

    # 멤버 추가 (생성자 포함)
    member_ids = set(room_data.member_ids)
    member_ids.add(current_user.id)

    for member_id in member_ids:
        member = ChatRoomMember(
            chat_room_id=chat_room.id,
            user_id=member_id
        )
        db.add(member)

    db.commit()
    db.refresh(chat_room)

    return {
        **chat_room.__dict__,
        "member_ids": list(member_ids)
    }

@router.get("/rooms", response_model=List[ChatRoomWithMembers])
def get_chat_rooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 현재 사용자가 속한 채팅방들
    memberships = db.query(ChatRoomMember).filter(
        ChatRoomMember.user_id == current_user.id
    ).all()

    chat_rooms = []
    for membership in memberships:
        room = membership.chat_room
        member_ids = [m.user_id for m in room.members]
        chat_rooms.append({
            **room.__dict__,
            "member_ids": member_ids
        })

    return chat_rooms

@router.get("/rooms/{room_id}", response_model=ChatRoomWithMembers)
def get_chat_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    # 사용자가 멤버인지 확인
    is_member = db.query(ChatRoomMember).filter(
        ChatRoomMember.chat_room_id == room_id,
        ChatRoomMember.user_id == current_user.id
    ).first()

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat room"
        )

    member_ids = [m.user_id for m in room.members]
    return {
        **room.__dict__,
        "member_ids": member_ids
    }

@router.delete("/rooms/{room_id}")
def delete_chat_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    db.delete(room)
    db.commit()
    return {"message": "Chat room deleted successfully"}

# ========== Message APIs ==========

@router.post("/messages", response_model=MessageResponse)
def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 채팅방 멤버 확인
    is_member = db.query(ChatRoomMember).filter(
        ChatRoomMember.chat_room_id == message_data.chat_room_id,
        ChatRoomMember.user_id == current_user.id
    ).first()

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat room"
        )

    # 메시지 생성
    message = Message(
        id=str(uuid4()),
        chat_room_id=message_data.chat_room_id,
        sender_id=current_user.id,
        sender_name=current_user.name,
        sender_role=current_user.role.value,
        type=message_data.type,
        content=message_data.content,
        file_url=message_data.file_url,
        file_name=message_data.file_name,
        parent_message_id=message_data.parent_message_id,
        feedback_ids=[]
    )

    db.add(message)

    # 피드백인 경우 원본 메시지의 feedback_ids 업데이트
    if message_data.parent_message_id:
        parent = db.query(Message).filter(Message.id == message_data.parent_message_id).first()
        if parent:
            if parent.feedback_ids is None:
                parent.feedback_ids = []
            parent.feedback_ids = parent.feedback_ids + [message.id]

    # 채팅방 updated_at 업데이트
    room = db.query(ChatRoom).filter(ChatRoom.id == message_data.chat_room_id).first()
    if room:
        room.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(message)

    return message

@router.get("/rooms/{room_id}/messages", response_model=List[MessageResponse])
def get_messages(
    room_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 멤버 확인
    is_member = db.query(ChatRoomMember).filter(
        ChatRoomMember.chat_room_id == room_id,
        ChatRoomMember.user_id == current_user.id
    ).first()

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat room"
        )

    messages = db.query(Message).filter(
        Message.chat_room_id == room_id
    ).order_by(Message.timestamp).offset(skip).limit(limit).all()

    return messages

# ========== Version APIs ==========

@router.post("/versions", response_model=VersionResponse)
def create_version(
    version_data: VersionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 채팅방의 현재 버전 번호 계산
    last_version = db.query(ChatVersion).filter(
        ChatVersion.chat_room_id == version_data.chat_room_id
    ).order_by(ChatVersion.version_number.desc()).first()

    version_number = 1 if not last_version else last_version.version_number + 1

    # 현재 채팅방의 모든 메시지 ID 가져오기
    messages = db.query(Message).filter(
        Message.chat_room_id == version_data.chat_room_id
    ).order_by(Message.timestamp).all()

    message_ids = [msg.id for msg in messages]

    # 버전 생성
    version = ChatVersion(
        id=str(uuid4()),
        chat_room_id=version_data.chat_room_id,
        version_number=version_number,
        description=version_data.description,
        created_by=current_user.id,
        message_ids=message_ids
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    return version

@router.get("/rooms/{room_id}/versions", response_model=List[VersionResponse])
def get_versions(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    versions = db.query(ChatVersion).filter(
        ChatVersion.chat_room_id == room_id
    ).order_by(ChatVersion.version_number.desc()).all()

    return versions

@router.get("/versions/{version_id}/messages", response_model=List[MessageResponse])
def get_version_messages(
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    version = db.query(ChatVersion).filter(ChatVersion.id == version_id).first()
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )

    # 버전에 저장된 메시지 ID들로 메시지 조회
    messages = db.query(Message).filter(
        Message.id.in_(version.message_ids)
    ).order_by(Message.timestamp).all()

    return messages


# ========== DM (Direct Message) APIs ==========

@router.post("/dm", response_model=ChatRoomResponse)
def create_dm(
    other_user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a DM (Direct Message) chat room between current user and another user.
    If already exists, return the existing DM.
    """
    # Cannot DM yourself
    if current_user.id == other_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create DM with yourself"
        )

    # Check if other user exists
    other_user = db.query(User).filter(User.id == other_user_id).first()
    if not other_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if DM already exists (either direction)
    existing_dm = db.query(ChatRoom).filter(
        ChatRoom.type == "dm",
        (
            ((ChatRoom.user1_id == current_user.id) & (ChatRoom.user2_id == other_user_id)) |
            ((ChatRoom.user1_id == other_user_id) & (ChatRoom.user2_id == current_user.id))
        )
    ).first()

    if existing_dm:
        return existing_dm

    # Create new DM
    dm = ChatRoom(
        id=str(uuid4()),
        name=f"DM: {current_user.name} - {other_user.name}",
        description="Direct Message",
        type="dm",
        user1_id=current_user.id,
        user2_id=other_user_id,
    )
    db.add(dm)
    db.commit()
    db.refresh(dm)

    return dm


@router.get("/dm/my", response_model=List[ChatRoomResponse])
def get_my_dms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all DMs where the current user is a participant.
    """
    dms = db.query(ChatRoom).filter(
        ChatRoom.type == "dm",
        (
            (ChatRoom.user1_id == current_user.id) |
            (ChatRoom.user2_id == current_user.id)
        )
    ).order_by(ChatRoom.updated_at.desc()).all()

    return dms


@router.get("/project/{project_id}", response_model=ChatRoomResponse)
def get_project_chat_room(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the chat room for a specific project.
    """
    from app.models.project import ProjectMember

    # Check if user is a member of the project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project"
        )

    # Get project chat room
    chat_room = db.query(ChatRoom).filter(
        ChatRoom.type == "project",
        ChatRoom.project_id == project_id
    ).first()

    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project chat room not found"
        )

    return chat_room
