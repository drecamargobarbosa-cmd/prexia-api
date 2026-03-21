from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.services.conversation_engine import ConversationEngine

app = FastAPI()

# permitir frontend acessar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversation_engine = ConversationEngine()


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()

    message = body.get("message", "")
    user_id = body.get("user_id", "default")

    result = conversation_engine.process(
        message=message,
        user_id=user_id
    )

    return result
