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

        if "otite" in q or "ouvido" in q or "otalgia" in q:
            return "otite_media_aguda"

        if "sinusite" in q:
            return "sinusite_bacteriana"

        if (
            "infeccao urinaria" in q
            or "infecção urinária" in q
            or "cistite" in q
            or "itu" in q
            or "disuria" in q
            or "disúria" in q
        ):
            return "itu_nao_complicada"

        if (
            "odonto" in q
            or "odontogenica" in q
            or "odontogênica" in q
            or "abscesso dentario" in q
            or "abscesso dentário" in q
            or "infeccao dentaria" in q
            or "infecção dentária" in q
            or "infeccao odontologica" in q
            or "infecção odontológica" in q
            or "dor de dente" in q
        ):
            return "infeccao_odontogenica"

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

    def has_no_allergy(self, texto: str) -> bool:
        expressoes = [
            "sem alergia",
            "sem alergias",
            "nega alergia",
            "nega alergias",
            "nao tem alergia",
            "nao tem alergias",
            "não tem alergia",
            "não tem alergias",
            "sem alergia a penicilina",
            "sem alergia a penicilina",
            "sem alergia a penicilina",
            "sem alergia a penicilina",
            "sem alergia a penicilina",
            "sem alergia a penicilina",
            "sem alergia a penicilina",
            "sem alergia a penicilina",
            "sem alergia a penicilina",
            "sem alergia à penicilina",
            "nega alergia a penicilina",
            "nega alergia à penicilina",
            "sem historia de alergia",
            "sem história de alergia",
        ]
        return any(expr in texto for expr in expressoes)

    def has_allergy(self, texto: str) -> bool:
        expressoes = [
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
            "tem alergia",
            "refere alergia",
            "historia de alergia",
            "história de alergia",
            "alergico",
            "alergica",
            "alérgico",
            "alérgica",
        ]
        return any(expr in texto for expr in expressoes)

    def has_severity(self, texto: str) -> bool:
        expressoes = [
            "febre alta",
            "toxemia",
            "toxico",
            "tóxico",
            "prostracao",
            "prostração",
            "dor intensa",
            "grave",
            "muito grave",
            "sinais de gravidade",
            "com gravidade",
        ]
        return any(expr in texto for expr in expressoes)

    def has_no_severity(self, texto: str) -> bool:
        expressoes = [
            "sem gravidade",
            "sem sinais de gravidade",
            "nao grave",
            "não grave",
            "leve",
            "sem febre alta",
            "sem toxemia",
        ]
        return any(expr in texto for expr in expressoes)

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
            if "10 mg/kg" in dose_base:
                dose_calculada = 10 * peso
                dose_final = f"{dose_calculada} mg/dia, baseado em {peso} kg"

            elif "5 mg/kg" in dose_base:
                dose_calculada = 5 * peso
                dose_final = f"{dose_calculada} mg/dia, baseado em {peso} kg"

            elif "50 a 90 mg/kg" in dose_base:
                min_dose = 50 * peso
                max_dose = 90 * peso
                dose_final = f"{min_dose} a {max_dose} mg/dia, baseado em {peso} kg"

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

    def evaluate(self, question: str, contexto: dict | None = None) -> dict:
        texto = normalize(question)

        idade = self.extract_idade(texto)
        peso = self.extract_peso(texto)

        sem_alergia = self.has_no_allergy(texto)
        tem_alergia = self.has_allergy(texto) and not sem_alergia

        sem_gravidade = self.has_no_severity(texto)
        tem_gravidade = self.has_severity(texto) and not sem_gravidade

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
                "antibiotico_sugerido": None,
                "dose": None,
                "duracao": None,
                "alternativas": [],
                "alertas_protocolo": [],
                "interacoes_medicamentosas": [],
                "red_flags": [],
                "confirmacao_necessaria": False,
                "perguntas_obrigatorias": [],
                "fonte": "protocolo_local_v1"
            }

        if contexto and contexto.get("scenario"):
            if scenario == "otite_media_aguda":
                faltando = []

                if idade is None:
                    faltando.append("Qual a idade do paciente?")

                if not tem_gravidade and not sem_gravidade:
                    faltando.append("Há sinais de gravidade, como febre alta, dor intensa ou toxemia?")

                if not tem_alergia and not sem_alergia:
                    faltando.append("O paciente tem alergia à penicilina?")

                if faltando:
                    return {
                        "tipo": "coleta_dados",
                        "cenario": scenario,
                        "resposta": "Ainda preciso de algumas informações para definir o tratamento:",
                        "perguntas": faltando
                    }

            return self.build_protocol_response(
                protocol=protocol,
                scenario=scenario,
                question=question,
                usar_alergia=tem_alergia,
                peso=peso,
            )

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
