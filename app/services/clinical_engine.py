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

    def evaluate(self, question: str, contexto: dict | None = None) -> dict:
        texto = normalize(question)

        # 🔴 Detectar alergia
        tem_alergia = any(p in texto for p in ["alergia", "alergico", "alérgico"])

        # 🔴 Detectar ausência de alergia
        sem_alergia = "sem alergia" in texto or "sem alergias" in texto

        # 🔴 Detectar gravidade (simples por enquanto)
        grave = any(p in texto for p in ["grave", "toxemia", "febre alta"])

        # 🔴 Cenário
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

        # 🔴 Se estamos na resposta do usuário
        if contexto and contexto.get("scenario"):

            primeira_linha = protocol.get("primeira_linha", {})
            alergia = protocol.get("alergia_penicilina", {})

            # 🔴 Decisão clínica básica
            if tem_alergia and not sem_alergia:
                medicamento = alergia.get("medicamento")
                dose = alergia.get("dose")
                duracao = alergia.get("duracao")
                justificativa = "Paciente com alergia à penicilina."
            else:
                medicamento = primeira_linha.get("medicamento")
                dose = primeira_linha.get("dose")
                duracao = primeira_linha.get("duracao")
                justificativa = "Primeira linha conforme protocolo."

            response = {
                "tipo": "protocolo",
                "cenario": scenario,
                "resposta": f"Protocolo definido. {justificativa}",
                "antibiotico_sugerido": medicamento,
                "dose": dose,
                "duracao": duracao,
                "alternativas": [],
                "alertas_protocolo": protocol.get("observacoes", []),
                "interacoes_medicamentosas": [],
                "red_flags": [],
                "confirmacao_necessaria": False,
                "perguntas_obrigatorias": [],
                "fonte": "protocolo_local_v1"
            }

            # 🔴 Interações
            drug_alerts = check_drug_interactions(question, medicamento)
            disease_alerts = check_disease_interactions(question, medicamento)

            response["interacoes_medicamentosas"] += drug_alerts
            response["alertas_protocolo"] += disease_alerts

            return response

        # 🔴 Fluxo inicial
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
    
