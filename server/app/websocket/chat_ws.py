from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
from sqlalchemy.orm import Session
from app.config import get_db
from app.models.user import User
from app.models.chat_room import ChatRoomMember
import json

class ConnectionManager:
    def __init__(self):
        # room_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # websocket -> user_id
        self.user_connections: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = []

        self.active_connections[room_id].append(websocket)
        self.user_connections[websocket] = user_id

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)

            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

        if websocket in self.user_connections:
            del self.user_connections[websocket]

    async def send_to_room(self, message: dict, room_id: str, exclude_ws: WebSocket = None):
        if room_id in self.active_connections:
            disconnected = []

            for connection in self.active_connections[room_id]:
                if connection == exclude_ws:
                    continue

                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            # 연결이 끊어진 웹소켓 제거
            for ws in disconnected:
                self.disconnect(ws, room_id)

    async def send_to_user(self, message: dict, user_id: str):
        for websocket, uid in self.user_connections.items():
            if uid == user_id:
                try:
                    await websocket.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    # 채팅방 멤버 확인
    is_member = db.query(ChatRoomMember).filter(
        ChatRoomMember.chat_room_id == room_id,
        ChatRoomMember.user_id == user_id
    ).first()

    if not is_member:
        await websocket.close(code=1008)  # Policy Violation
        return

    await manager.connect(websocket, room_id, user_id)

    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # 같은 채팅방의 다른 사용자들에게 브로드캐스트
            # 실제 DB 저장은 REST API(/api/chat/messages)에서 처리
            await manager.send_to_room(
                message={
                    "type": message_data.get("type", "message"),
                    "data": message_data
                },
                room_id=room_id,
                exclude_ws=None  # 본인에게도 전송 (확인용)
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

        # 사용자가 나갔다는 알림
        await manager.send_to_room(
            message={
                "type": "user_left",
                "data": {"user_id": user_id}
            },
            room_id=room_id
        )
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, room_id)
