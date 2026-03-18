from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.clinical_engine import ClinicalEngine


app = FastAPI(title="PREXIA API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatContext(BaseModel):
    scenario: Optional[str] = None
    collected_data: Optional[str] = None


class ChatRequest(BaseModel):
    mensagem: str
    contexto: Optional[ChatContext] = None


clinical_engine = ClinicalEngine()


@app.get("/")
def root():
    return {"status": "ok", "service": "prexia-api"}


@app.post("/chat")
def chat(request: ChatRequest):
    contexto_dict = request.contexto.model_dump() if request.contexto else None
    resultado = clinical_engine.evaluate(request.mensagem, contexto_dict)
    return resultado
