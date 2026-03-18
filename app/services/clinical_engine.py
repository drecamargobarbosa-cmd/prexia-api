from app.services.protocol_engine import ProtocolEngine
from app.services.response_engine import ResponseEngine
from app.services.safety_engine import normalize
from app.services.interaction_engine import (
    check_drug_interactions,
    check_disease_interactions,
)


class ClinicalEngine:

    def __init__(self):
        self.protocol_engine = ProtocolEngine()
        self.response_engine = ResponseEngine()

    def identify_scenario(self, question: str) -> str | None:
        q = normalize(question)

        if "otite" in q or "ouvido" in q:
            return "otite_media_aguda"

        if "sinusite" in q:
            return "sinusite_bacteriana"

        if (
            "infeccao urinaria" in q
            or "cistite" in q
            or "itu" in q
            or "disuria" in q
        ):
            return "itu_nao_complicada"

        if (
            "odonto" in q
            or "odontogenica" in q
            or "abscesso dentario" in q
            or "infeccao dentaria" in q
            or "dor de dente" in q
        ):
            return "infeccao_odontogenica"

        return None

    def evaluate(self, question: str, contexto: dict = None) -> dict:

        # 🔴 NOVO: usar contexto se existir
        if contexto and contexto.get("scenario"):
            scenario = contexto.get("scenario")
        else:
            scenario = self.identify_scenario(question)

        protocol = self.protocol_engine.load_protocol(scenario)

        if not protocol:
            return {
                "tipo": "sem_protocolo",
                "cenario": scenario,
                "resposta": "Nao tenho protocolo para esse cenario no momento.",
            }

        # 🔴 Se veio resposta do usuário, seguimos com decisão clínica
        if contexto and contexto.get("scenario"):
            response = self.response_engine.build_response(protocol, scenario)

            antibiotic = response.get("antibiotico_sugerido")

            drug_alerts = check_drug_interactions(question, antibiotic)
            disease_alerts = check_disease_interactions(question, antibiotic)

            existing_alerts = response.get("interacoes_medicamentosas", [])
            response["interacoes_medicamentosas"] = existing_alerts + drug_alerts

            existing_protocol_alerts = response.get("alertas_protocolo", [])
            response["alertas_protocolo"] = existing_protocol_alerts + disease_alerts

            return response

        # 🔴 Fluxo inicial (sem dados ainda)
        response = self.response_engine.build_response(protocol, scenario)

        perguntas = response.get("perguntas_obrigatorias", [])

        if perguntas:
            return {
                "tipo": "coleta_dados",
                "cenario": scenario,
                "resposta": "Antes de sugerir o tratamento, preciso de algumas informações:",
                "perguntas": perguntas
            }

        return response
    
