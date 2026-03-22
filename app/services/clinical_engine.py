import re
from copy import deepcopy
from app.services.protocol_engine import ProtocolEngine
from app.services.reasoning_engine import ReasoningEngine

from app.services.interaction_engine import (
    check_drug_interactions,
    check_disease_interactions
)


class ClinicalEngine:
    def __init__(self):
        self.protocol_engine = ProtocolEngine()
        self.reasoning_engine = ReasoningEngine()

        self.check_drug_interactions = check_drug_interactions
        self.check_disease_interactions = check_disease_interactions

    def evaluate(self, question: str, contexto: dict = None, user_id: str = "default"):
        if contexto is None:
            contexto = {}

        merged_context = self._ensure_context_structure(deepcopy(contexto))

        # Detectar cenário
        scenario = merged_context.get("scenario")
        if not scenario:
            scenario = self._detect_scenario(question)
            if scenario:
                merged_context["scenario"] = scenario

        # Extrair dados clínicos
        merged_context = self._extract_and_update_clinical_data(question, merged_context)

        # Histórico
        merged_context["history"].append({
            "role": "user",
            "content": question
        })

        # 🧠 NOVO: RACIOCÍNIO CLÍNICO
        reasoning = self.reasoning_engine.evaluate_readiness(merged_context)

        # 🚨 CASO 1: dados insuficientes
        if reasoning["status"] == "insufficient_data":
            resposta = "Preciso entender melhor o quadro clínico."
            return self._build_basic_response(resposta, merged_context, "coleta_dados")

        # ❓ CASO 2: precisa de mais dados
        if reasoning["status"] == "need_more_data":
            perguntas = reasoning.get("missing", [])
            resposta = "Ainda preciso de algumas informações:"
            return {
                "resposta": resposta,
                "clinical_response": {
                    "tipo": "coleta_dados",
                    "perguntas": perguntas
                },
                "context": merged_context
            }

        # ✅ CASO 3: pronto para tratar
        if reasoning["status"] == "ready_for_treatment":
            protocol = self.protocol_engine.generate_recommendation(
                scenario=merged_context.get("scenario"),
                dados_clinicos=merged_context.get("dados_clinicos")
            )

            resposta = protocol.get("resposta", "Conduta definida.")

            # 🔍 Interações
            interacoes = self.check_drug_interactions(
                question,
                protocol.get("medicacao")
            )

            doencas = self.check_disease_interactions(
                question,
                protocol.get("medicacao")
            )

            alertas = interacoes + doencas

            if alertas:
                resposta += "\n\nAtenção:\n" + "\n".join(alertas)

            return {
                "resposta": resposta,
                "clinical_response": {
                    "tipo": "conduta",
                    "cenario": merged_context.get("scenario"),
                    "alertas": alertas
                },
                "context": merged_context
            }

        # fallback
        return self._build_basic_response(
            "Não consegui definir conduta com segurança.",
            merged_context,
            "erro"
        )

    def _build_basic_response(self, resposta, contexto, tipo):
        return {
            "resposta": resposta,
            "clinical_response": {
                "tipo": tipo
            },
            "context": contexto
        }

    def _ensure_context_structure(self, context: dict) -> dict:
        if "history" not in context:
            context["history"] = []

        if "dados_clinicos" not in context:
            context["dados_clinicos"] = {}

        return context

    def _normalize(self, text: str) -> str:
        if not text:
            return ""
        return text.lower()

    def _detect_scenario(self, text: str):
        t = self._normalize(text)

        if "ouvido" in t or "otite" in t:
            return "otite_media_aguda"

        if "sinusite" in t:
            return "sinusite"

        if "garganta" in t:
            return "faringoamigdalite"

        return None

    def _extract_and_update_clinical_data(self, text: str, context: dict) -> dict:
        dados = context["dados_clinicos"]
        t = self._normalize(text)

        if "febre" in t:
            dados["febre"] = True

        if "sem febre" in t:
            dados["febre"] = False

        if "alergia" in t:
            dados["alergia"] = True

        if "sem alergia" in t:
            dados["alergia"] = False

        if "grave" in t:
            dados["gravidade"] = True

        context["dados_clinicos"] = dados
        return context
