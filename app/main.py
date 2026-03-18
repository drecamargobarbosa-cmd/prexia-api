from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from app.services.clinical_engine import recommend_antibiotic
from app.services.interaction_engine import check_drug_interactions, check_disease_interactions
from app.services.safety_engine import compare_with_protocol, build_final_response

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
    clinical_data = recommend_antibiotic(request.mensagem)
    recommended_name = clinical_data["recommended"]["medicamento"] if clinical_data["recommended"] else None

    drug_alerts = check_drug_interactions(request.mensagem, recommended_name)
    disease_alerts = check_disease_interactions(request.mensagem, recommended_name)
    safety_data = compare_with_protocol(clinical_data["proposed"], clinical_data["recommended"])

    return build_final_response(clinical_data, drug_alerts, disease_alerts, safety_data)
