from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.services.clinical_engine import ClinicalEngine

app = FastAPI()

# permitir frontend acessar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clinical_engine = ClinicalEngine()


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()

    message = body.get("message", "")
    user_id = body.get("user_id", "default")

    # 🔴 NÃO CONFIE NO CONTEXTO DO FRONTEND
    # Isso estava quebrando tudo
    contexto = {}

    result = clinical_engine.evaluate(
        question=message,
        contexto=contexto,
        user_id=user_id
    )

    return result
