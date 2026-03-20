from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.clinical_engine import ClinicalEngine
from app.services.session_memory import (
    add_message,
    get_context,
    get_history,
    update_context,
    clear_history,
)


app = FastAPI(title="PREXIA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clinical_engine = ClinicalEngine()


class ChatRequest(BaseModel):
    user_id: str
    message: str


@app.get("/")
def root():
    return {"status": "ok", "service": "PREXIA API"}


@app.post("/chat")
def chat(request: ChatRequest):
    user_id = request.user_id
    message = request.message

    add_message(user_id, "user", message)

    contexto_atual = get_context(user_id)

    clinical_response = clinical_engine.evaluate(
        question=message,
        contexto=contexto_atual,
    )

    update_context(
        user_id,
        {
            "scenario": clinical_response.get("cenario"),
            "dados_clinicos": clinical_response.get("dados_clinicos", {}),
        },
    )

    resposta_texto = clinical_response.get("resposta", "")

    add_message(user_id, "assistant", resposta_texto)

    return {
        "resposta": resposta_texto,
        "clinical_response": clinical_response,
        "history": get_history(user_id),
        "context": get_context(user_id),
    }


@app.post("/reset/{user_id}")
def reset_user_context(user_id: str):
    clear_history(user_id)
    return {
        "status": "ok",
        "message": "Contexto apagado"
    }
