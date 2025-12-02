from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.config import Base, engine, get_db
from app.api import auth, users, chat, projects
from app.websocket.chat_ws import websocket_endpoint

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Research Chat API",
    description="연구실 협업 메신저 API",
    version="1.0.0"
)

# CORS 설정 (Flutter 앱에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API 라우터 등록
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(projects.router)

# WebSocket 엔드포인트
@app.websocket("/ws/{room_id}/{user_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    await websocket_endpoint(websocket, room_id, user_id, db)

@app.get("/")
def root():
    return {
        "message": "Research Chat API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
