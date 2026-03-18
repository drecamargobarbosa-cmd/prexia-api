from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="Prexia API",
    description="API clínica para suporte à decisão médica",
    version="1.0"
)

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
    mensagem = request.mensagem.lower()

    if "sinusite" in mensagem and "penicilina" in mensagem:
        return {
            "resposta": "Para sinusite bacteriana em paciente com alergia a penicilina, uma alternativa frequentemente considerada é azitromicina. Confirmar gravidade, histórico de reação, diretriz local e risco de resistência bacteriana.",
            "tipo": "recomendacao_inicial",
            "fonte": "motor_clinico_inicial"
        }

    if "sinusite" in mensagem:
        return {
            "resposta": "Para sinusite bacteriana, uma opção de primeira linha frequentemente utilizada é amoxicilina com clavulanato, considerando diretriz local, gravidade, idade, alergias e comorbidades.",
            "tipo": "recomendacao_inicial",
            "fonte": "motor_clinico_inicial"
        }

    return {
        "resposta": "Ainda não tenho protocolo estruturado para esse cenário. Posso evoluir para analisar diagnósticos como sinusite, otite, ITU, pneumonia comunitária e infecção odontogênica.",
        "tipo": "fallback",
        "fonte": "motor_clinico_inicial"
    }
