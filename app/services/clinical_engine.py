import re

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

        return None

    def extract_peso(self, texto: str):
        match = re.search(r'(\d+)\s?kg', texto)
        if match:
            return int(match.group(1))
        return None

    def extract_idade(self, texto: str):
        match = re.search(r'(\d+)\s?anos?', texto)
        if match:
            return int(match.group(1))
        return None

    def detect_allergy(self, texto: str):
        if any(p in texto for p in ["sem alergia", "nega alergia"]):
            return False
        if "alerg" in texto:
            return True
        return None

    def detect_severity(self, texto: str):
        if "sem gravidade" in texto:
            return False
        if any(p in texto for p in ["grave", "febre alta", "toxemia"]):
            return True
        return None

    def evaluate(self, question: str, contexto: dict | None = None) -> dict:

        contexto = contexto or {}

        # 🔴 DADOS JÁ EXISTENTES
        dados = contexto.get("dados_clinicos", {
            "idade": None,
            "peso": None,
            "alergia": None,
            "gravidade": None
        })

        texto = normalize(question)

        # 🔴 ATUALIZA APENAS O QUE FOI IDENTIFICADO
        idade = self.extract_idade(texto)
        if idade is not None:
            dados["idade"] = idade

        peso = self.extract_peso(texto)
        if peso is not None:
            dados["peso"] = peso

        alergia = self.detect_allergy(texto)
        if alergia is not None:
            dados["alergia"] = alergia

        gravidade = self.detect_severity(texto)
        if gravidade is not None:
            dados["gravidade"] = gravidade

        # 🔴 CENÁRIO
        scenario = contexto.get("scenario") or self.identify_scenario(question)

        protocol = self.protocol_engine.load_protocol(scenario)

        if not protocol:
            return {
                "tipo": "sem_protocolo",
                "resposta": "Nao tenho protocolo para esse cenario no momento.",
                "cenario": scenario,
                "dados_clinicos": dados
            }

        # 🔴 VERIFICA O QUE FALTA
        faltando = []

        if dados["idade"] is None:
            faltando.append("Qual a idade do paciente?")

        if dados["gravidade"] is None:
            faltando.append("Há sinais de gravidade?")

        if dados["alergia"] is None:
            faltando.append("O paciente tem alergia à penicilina?")

        if faltando:
            return {
                "tipo": "coleta_dados",
                "cenario": scenario,
                "resposta": "Ainda preciso de algumas informações para definir o tratamento:",
                "perguntas": faltando,
                "dados_clinicos": dados
            }

        # 🔴 DECISÃO FINAL
        if dados["alergia"]:
            protocolo = protocol.get("alergia_penicilina", {})
            justificativa = "Paciente com alergia à penicilina."
        else:
            protocolo = protocol.get("primeira_linha", {})
            justificativa = "Primeira linha conforme protocolo."

        medicamento = protocolo.get("medicamento")
        dose_base = protocolo.get("dose")
        duracao = protocolo.get("duracao")

        # 🔴 CÁLCULO DE DOSE
        dose_final = dose_base

        if dados["peso"] and dose_base:
            if "50 a 90 mg/kg" in dose_base:
                min_dose = 50 * dados["peso"]
                max_dose = 90 * dados["peso"]
                dose_final = f"{min_dose} a {max_dose} mg/dia baseado em {dados['peso']} kg"

            elif "10 mg/kg" in dose_base:
                dose_final = f"{10 * dados['peso']} mg/dia"

        return {
            "tipo": "protocolo",
            "cenario": scenario,
            "resposta": f"Protocolo definido. {justificativa}",
            "antibiotico_sugerido": medicamento,
            "dose": dose_final,
            "duracao": duracao,
            "alertas_protocolo": protocol.get("observacoes", []),
            "dados_clinicos": dados
        }
