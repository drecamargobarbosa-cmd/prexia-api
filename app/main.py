from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from app.services.clinical_engine import ClinicalEngine

app = FastAPI(
    title="Prexia API",
    description="API clínica para suporte à decisão médica",
    version="1.0"
)

clinical_engine = ClinicalEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    mensagem: str
    contexto: List[str] = []

@app.get("/")
def root():
    return {"message": "Prexia API running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(request: ChatRequest):
    return clinical_engine.evaluate(request.mensagem)
