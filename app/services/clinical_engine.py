from app.services.protocol_engine import ProtocolEngine
from app.services.response_engine import ResponseEngine
from app.services.safety_engine import normalize
from app.services.interaction_engine import (
    check_drug_interactions,
    check_disease_interactions,
)
import re


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

    def extract_peso(self, texto: str):
        match = re.search(r'(\d+)\s?kg', texto)
        if match:
            return int(match.group(1))
        return None

    def evaluate(self, question: str, contexto: dict | None = None) -> dict:
        texto = normalize(question)

        # 🔴 Detectar alergia
        tem_alergia = any(p in texto for p in ["alergia", "alergico", "alérgico"])

        # 🔴 Detectar ausência de alergia
        sem_alergia = "sem alergia" in texto or "sem alergias" in texto

        # 🔴 Extrair peso
        peso = self.extract_peso(texto)

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

        # 🔴 Fluxo com resposta do usuário
        if contexto and contexto.get("scenario"):

            primeira_linha = protocol.get("primeira_linha", {})
            alergia = protocol.get("alergia_penicilina", {})

            if tem_alergia and not sem_alergia:
                medicamento = alergia.get("medicamento")
                dose_base = alergia.get("dose")
                duracao = alergia.get("duracao")
                justificativa = "Paciente com alergia à penicilina."
            else:
                medicamento = primeira_linha.get("medicamento")
                dose_base = primeira_linha.get("dose")
                duracao = primeira_linha.get("duracao")
                justificativa = "Primeira linha conforme protocolo."

            # 🔴 Calcular dose se tiver peso
            dose_final = dose_base

            if peso and "mg/kg" in dose_base:
                if "10 mg/kg" in dose_base:
                    dose_calculada = 10 * peso
                    dose_final = f"{dose_calculada} mg/dia (baseado em {peso} kg)"
                elif "5 mg/kg" in dose_base:
                    dose_calculada = 5 * peso
                    dose_final = f"{dose_calculada} mg/dia (baseado em {peso} kg)"
                elif "50 a 90 mg/kg" in dose_base:
                    min_dose = 50 * peso
                    max_dose = 90 * peso
                    dose_final = f"{min_dose} a {max_dose} mg/dia (baseado em {peso} kg)"

            response = {
                "tipo": "protocolo",
                "cenario": scenario,
                "resposta": f"Protocolo definido. {justificativa}",
                "antibiotico_sugerido": medicamento,
                "dose": dose_final,
                "duracao": duracao,
                "alternativas": [],
                "alertas_protocolo": protocol.get("observacoes", []),
                "interacoes_medicamentosas": [],
                "red_flags": [],
                "confirmacao_necessaria": False,
                "perguntas_obrigatorias": [],
                "fonte": "protocolo_local_v1"
            }

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
    
