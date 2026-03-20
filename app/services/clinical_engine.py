import re

from app.protocols.antibiotics import ANTIBIOTIC_PROTOCOLS
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

        for scenario, protocol in ANTIBIOTIC_PROTOCOLS.items():
            keywords = protocol.get("keywords", [])
            for keyword in keywords:
                if normalize(keyword) in q:
                    return scenario

        return None

    def extract_peso(self, texto: str) -> int | None:
        match = re.search(r'(\d+)\s?kg\b', texto)
        if match:
            return int(match.group(1))
        return None

    def extract_idade(self, texto: str) -> int | None:
        patterns = [
            r'(\d+)\s?anos\b',
            r'(\d+)\s?ano\b',
            r'(\d+)\s?a\b',
        ]

        for pattern in patterns:
            match = re.search(pattern, texto)
            if match:
                return int(match.group(1))

        return None

    def detect_allergy(self, texto: str) -> bool | None:
        texto = normalize(texto)

        termos_negacao = [
            "sem alergia",
            "sem alergias",
            "nega alergia",
            "nega alergias",
            "nao tem alergia",
            "nao tem alergias",
            "não tem alergia",
            "não tem alergias",
            "sem alergia a penicilina",
            "sem alergia à penicilina",
            "nega alergia a penicilina",
            "nega alergia à penicilina",
        ]

        termos_presenca = [
            "alergia a penicilina",
            "alergia à penicilina",
            "alergico a penicilina",
            "alergico à penicilina",
            "alergica a penicilina",
            "alergica à penicilina",
            "alérgico a penicilina",
            "alérgico à penicilina",
            "alérgica a penicilina",
            "alérgica à penicilina",
            "alergico",
            "alergica",
            "alérgico",
            "alérgica",
            "tem alergia",
            "refere alergia",
        ]

        if any(t in texto for t in termos_negacao):
            return False

        if any(t in texto for t in termos_presenca):
            return True

        return None

    def detect_severity(self, texto: str) -> bool | None:
        texto = normalize(texto)

        termos_negacao = [
            "sem gravidade",
            "sem sinais de gravidade",
            "nao grave",
            "não grave",
            "leve",
            "sem febre alta",
            "sem toxemia",
        ]

        termos_presenca = [
            "grave",
            "muito grave",
            "febre alta",
            "toxemia",
            "dor intensa",
            "prostracao",
            "prostração",
            "com gravidade",
            "sinais de gravidade",
        ]

        if any(t in texto for t in termos_negacao):
            return False

        if any(t in texto for t in termos_presenca):
            return True

        return None

    def build_alternatives(
        self,
        protocol: dict,
        medicamento_escolhido: str | None,
    ) -> list[str]:
        alternativas = []

        alternativa = protocol.get("alternativa", {})
        alergia_penicilina = protocol.get("alergia_penicilina", {})

        for opcao in [alternativa, alergia_penicilina]:
            medicamento = opcao.get("medicamento")
            if not medicamento:
                continue

            if medicamento_escolhido and normalize(medicamento) == normalize(medicamento_escolhido):
                continue

            if medicamento not in alternativas:
                alternativas.append(medicamento)

        return alternativas

    def build_protocol_response(
        self,
        protocol: dict,
        scenario: str,
        question: str,
        usar_alergia: bool = False,
        peso: int | None = None,
    ) -> dict:
        primeira_linha = protocol.get("primeira_linha", {})
        alergia = protocol.get("alergia_penicilina", {})

        if usar_alergia and alergia:
            medicamento = alergia.get("medicamento")
            dose_base = alergia.get("dose")
            duracao = alergia.get("duracao")
            justificativa = "Paciente com alergia à penicilina."
        else:
            medicamento = primeira_linha.get("medicamento")
            dose_base = primeira_linha.get("dose")
            duracao = primeira_linha.get("duracao")
            justificativa = "Primeira linha conforme protocolo."

        dose_final = dose_base

        if peso and dose_base:
            if "50 a 90 mg/kg" in dose_base:
                min_dose = 50 * peso
                max_dose = 90 * peso
                dose_final = f"{min_dose} a {max_dose} mg/dia, baseado em {peso} kg"
            elif "10 mg/kg" in dose_base:
                dose_calculada = 10 * peso
                dose_final = f"{dose_calculada} mg/dia, baseado em {peso} kg"
            elif "5 mg/kg" in dose_base:
                dose_calculada = 5 * peso
                dose_final = f"{dose_calculada} mg/dia, baseado em {peso} kg"

        alternativas = self.build_alternatives(
            protocol=protocol,
            medicamento_escolhido=medicamento,
        )

        response = {
            "tipo": "protocolo",
            "cenario": scenario,
            "resposta": f"Protocolo definido. {justificativa}",
            "antibiotico_sugerido": medicamento,
            "dose": dose_final,
            "duracao": duracao,
            "alternativas": alternativas,
            "alertas_protocolo": protocol.get("observacoes", []),
            "interacoes_medicamentosas": [],
            "red_flags": [],
            "confirmacao_necessaria": False,
            "perguntas_obrigatorias": protocol.get("perguntas_obrigatorias", []),
            "fonte": "protocolo_local_v1"
        }

        drug_alerts = check_drug_interactions(question, medicamento)
        disease_alerts = check_disease_interactions(question, medicamento)

        response["interacoes_medicamentosas"] += drug_alerts
        response["alertas_protocolo"] += disease_alerts

        return response

    def evaluate(self, question: str, contexto: dict | None = None) -> dict:
        contexto = contexto or {}

        dados = contexto.get("dados_clinicos") or {
            "idade": None,
            "peso": None,
            "alergia": None,
            "gravidade": None,
        }

        texto = normalize(question)

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

        scenario = contexto.get("scenario")
        if not scenario:
            scenario = self.identify_scenario(question)

        protocol = self.protocol_engine.load_protocol(scenario)

        if not protocol:
            return {
                "tipo": "sem_protocolo",
                "cenario": scenario,
                "resposta": "Nao tenho protocolo para esse cenario no momento.",
                "antibiotico_sugerido": None,
                "dose": None,
                "duracao": None,
                "alternativas": [],
                "alertas_protocolo": [],
                "interacoes_medicamentosas": [],
                "red_flags": [],
                "confirmacao_necessaria": False,
                "perguntas_obrigatorias": [],
                "fonte": "protocolo_local_v1",
                "dados_clinicos": dados
            }

        perguntas_obrigatorias = protocol.get("perguntas_obrigatorias", [])

        faltando = []

        for pergunta in perguntas_obrigatorias:
            pergunta_n = normalize(pergunta)

            if "idade" in pergunta_n and dados["idade"] is None:
                faltando.append(pergunta)
            elif "gravidade" in pergunta_n and dados["gravidade"] is None:
                faltando.append(pergunta)
            elif "alergia" in pergunta_n and dados["alergia"] is None:
                faltando.append(pergunta)
            elif "peso" in pergunta_n and dados["peso"] is None:
                faltando.append(pergunta)

        if faltando:
            return {
                "tipo": "coleta_dados",
                "cenario": scenario,
                "resposta": "Ainda preciso de algumas informações para definir o tratamento:",
                "perguntas": faltando,
                "dados_clinicos": dados
            }

        return self.build_protocol_response(
            protocol=protocol,
            scenario=scenario,
            question=question,
            usar_alergia=bool(dados["alergia"]),
            peso=dados["peso"],
        ) | {
            "dados_clinicos": dados
        }
