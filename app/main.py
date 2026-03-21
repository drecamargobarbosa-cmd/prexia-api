from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.conversation_engine import ConversationEngine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversation_engine = ConversationEngine()


class ChatRequest(BaseModel):
    user_id: str = "default"
    message: str


@app.post("/chat")
async def chat(payload: ChatRequest):
    result = conversation_engine.process(
        message=payload.message,
        user_id=payload.user_id
    )
    return result


@app.post("/reset/{user_id}")
async def reset_conversation(user_id: str):
    conversation_engine.memory_service.clear(user_id)
    return {
        "status": "ok",
        "message": f"Contexto do usuário {user_id} removido com sucesso."
    }
