from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.clinical_engine import ClinicalEngine
from app.services.session_memory import add_message, get_history


app = FastAPI(title="PREXIA API", version="1.1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chat.prexia.com.br",
        "https://prexia.com.br",
        "https://www.prexia.com.br",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatContext(BaseModel):
    scenario: Optional[str] = None
    collected_data: Optional[str] = None


class ChatRequest(BaseModel):
    user_id: str
    mensagem: str
    contexto: Optional[ChatContext] = None


clinical_engine = ClinicalEngine()


@app.get("/")
def root():
    return {"status": "ok", "service": "prexia-api"}


@app.post("/chat")
def chat(request: ChatRequest):
    contexto_dict = request.contexto.model_dump() if request.contexto else {}

    add_message(
        user_id=request.user_id,
        role="user",
        content=request.mensagem
    )

    historico = get_history(request.user_id)

    if historico:
        ultimas_mensagens = historico[-6:]
        contexto_historico = "\n".join(
            [f"{item['role']}: {item['content']}" for item in ultimas_mensagens]
        )
        contexto_dict["conversation_history"] = contexto_historico

    resultado = clinical_engine.evaluate(request.mensagem, contexto_dict)

    resposta_assistente = resultado.get("answer") or resultado.get("resposta") or str(resultado)

    add_message(
        user_id=request.user_id,
        role="assistant",
        content=resposta_assistente
    )

    return resultado
