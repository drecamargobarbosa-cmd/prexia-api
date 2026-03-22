import re
from copy import deepcopy
from app.services.protocol_engine import ProtocolEngine

# NOVO: integração com interaction_engine
from app.services.interaction_engine import (
    check_drug_interactions,
    check_disease_interactions
)


class ClinicalEngine:
    def __init__(self):
        self.protocol_engine = ProtocolEngine()

        # NOVO: armazenar funções de interação
        self.check_drug_interactions = check_drug_interactions
        self.check_disease_interactions = check_disease_interactions

    def evaluate(self, question: str, contexto: dict = None, user_id: str = "default"):
        if contexto is None:
            contexto = {}

        merged_context = self._ensure_context_structure(deepcopy(contexto))

        scenario = merged_context.get("scenario")
        if not scenario:
            scenario = self._detect_scenario(question)
            if scenario:
                merged_context["scenario"] = scenario

        merged_context = self._extract_and_update_clinical_data(question, merged_context)

        intent = self._detect_intent(question)
        merged_context["intent"] = intent

        merged_context["history"].append({
            "role": "user",
            "content": question
        })

        response = self._build_response(merged_context, question)

        merged_context["history"].append({
            "role": "assistant",
            "content": response["resposta"]
        })

        response["history"] = merged_context["history"]
        response["context"] = merged_context

        return response

    def _ensure_context_structure(self, context: dict) -> dict:
        if "history" not in context or not isinstance(context["history"], list):
            context["history"] = []

        if "dados_clinicos" not in context or not isinstance(context["dados_clinicos"], dict):
            context["dados_clinicos"] = {}

        defaults = {
            "idade": None,
            "peso": None,
            "alergia": None,
            "gravidade": None,
            "febre": None,
            "febre_alta": None,
            "dor_presente": None,
            "dor_intensa": None,
            "toxemia": None,
            "prostracao": None,
            "secrecao_auricular": None,
            "secrecao_purulenta": None,
            "duracao_dias": None
        }

        for key, value in defaults.items():
            if key not in context["dados_clinicos"]:
                context["dados_clinicos"][key] = value

        if "scenario" not in context:
            context["scenario"] = None

        if "intent" not in context:
            context["intent"] = "geral"

        return context

    def _normalize(self, text: str) -> str:
        if not text:
            return ""

        text = text.strip().lower()

        replacements = {
            "á": "a", "à": "a", "ã": "a", "â": "a",
            "é": "e", "ê": "e",
            "í": "i",
            "ó": "o", "ô": "o", "õ": "o",
            "ú": "u",
            "ç": "c"
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _detect_scenario(self, text: str):
        t = self._normalize(text)

        if "ouvido" in t or "otite" in t:
            return "otite_media_aguda"

        if "sinusite" in t:
            return "sinusite"

        if "garganta" in t:
            return "faringoamigdalite"

        return None

    def _detect_intent(self, text: str):
        t = self._normalize(text)

        if "dose" in t or "posologia" in t:
            return "dose"

        if "antibiotico" in t:
            return "antibiotico"

        if "tratamento" in t:
            return "tratamento"

        return "geral"

    def _extract_and_update_clinical_data(self, text: str, context: dict) -> dict:
        dados = context["dados_clinicos"]
        t = self._normalize(text)

        if "sem alergia" in t:
            dados["alergia"] = False
        elif "alergia" in t:
            dados["alergia"] = True

        if "febre" in t:
            dados["febre"] = True
        if "sem febre" in t:
            dados["febre"] = False

        if "grave" in t:
            dados["gravidade"] = True
        if "sem gravidade" in t:
            dados["gravidade"] = False

        context["dados_clinicos"] = dados
        return context

    def _build_response(self, context: dict, question: str) -> dict:
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})

        if not scenario:
            return {
                "resposta": "Preciso entender melhor o quadro clínico.",
                "clinical_response": {
                    "tipo": "coleta_dados"
                }
            }

        protocol = self.protocol_engine.generate_recommendation(
            scenario=scenario,
            dados_clinicos=dados
        )

        resposta = protocol.get("resposta", "Conduta definida.")

        # NOVO: checar interações
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
                "cenario": scenario,
                "dados_clinicos": dados,
                "alertas": alertas
            }
        }
