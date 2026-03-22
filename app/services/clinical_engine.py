import re
import unicodedata
from copy import deepcopy

from app.services.reasoning_engine import ReasoningEngine
from app.services.decision_engine import DecisionEngine


class ClinicalEngine:
    """
    Orquestrador clínico.

    Responsabilidades:
    - manter contexto e histórico
    - detectar ou trocar cenário clínico
    - extrair dados clínicos da fala do usuário
    - chamar o reasoning_engine para avaliar prontidão
    - chamar o decision_engine quando houver base suficiente
    """

    def __init__(self):
        self.reasoning_engine = ReasoningEngine()
        self.decision_engine = DecisionEngine()

    def evaluate(self, question: str, contexto: dict = None, user_id: str = "default"):
        if contexto is None:
            contexto = {}

        merged_context = self._ensure_context_structure(deepcopy(contexto))
        normalized_question = self._normalize(question)

        detected_scenario = self._detect_scenario(normalized_question)
        if detected_scenario and detected_scenario != merged_context.get("scenario"):
            merged_context["scenario"] = detected_scenario

        merged_context = self._extract_and_update_clinical_data(question, merged_context)
        merged_context["intent"] = self._detect_intent(normalized_question)

        merged_context["history"].append({
            "role": "user",
            "content": question
        })

        reasoning = self.reasoning_engine.evaluate_readiness(merged_context)

        response = self._build_response(
            question=question,
            context=merged_context,
            reasoning=reasoning
        )

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
            "duracao_dias": None,
            "dor_garganta": None,
            "placas_amigdalianas": None,
            "dor_facial": None,
            "secrecao_nasal_purulenta": None
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
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        return text

    def _contains_any(self, text: str, terms: list[str]) -> bool:
        return any(term in text for term in terms)

    def _detect_scenario(self, normalized_text: str):
        if self._contains_any(normalized_text, [
            "dor de ouvido", "dor no ouvido", "otalgia", "otite", "ouvido doendo"
        ]):
            return "otite_media_aguda"

        if self._contains_any(normalized_text, [
            "dor de garganta", "garganta", "odinofagia", "amigdalite", "faringite", "faringoamigdalite"
        ]):
            return "faringoamigdalite"

        if self._contains_any(normalized_text, [
            "sinusite", "dor facial", "seios da face", "pressao na face"
        ]):
            return "sinusite"

        return None

    def _detect_intent(self, normalized_text: str):
        if self._contains_any(normalized_text, [
            "qual a dose", "qual dose", "dose", "dosagem", "posologia"
        ]):
            return "dose"

        if self._contains_any(normalized_text, [
            "antibiotico", "qual antibiotico"
        ]):
            return "antibiotico"

        if self._contains_any(normalized_text, [
            "medicamento", "qual medicamento", "qual remedio", "remedio"
        ]):
            return "medicamento"

        if self._contains_any(normalized_text, [
            "tratamento", "qual conduta", "conduta"
        ]):
            return "tratamento"

        return "geral"

    def _extract_and_update_clinical_data(self, text: str, context: dict) -> dict:
        dados = context["dados_clinicos"]
        t = self._normalize(text)

        idade = self._extract_age(t)
        if idade is not None:
            dados["idade"] = idade

        peso = self._extract_weight(t)
        if peso is not None:
            dados["peso"] = peso

        duracao = self._extract_duration_days(t)
        if duracao is not None:
            dados["duracao_dias"] = duracao

        alergia = self._extract_allergy_status(t)
        if alergia is not None:
            dados["alergia"] = alergia

        febre = self._extract_fever_status(t)
        if febre is not None:
            dados["febre"] = febre

        gravidade = self._extract_explicit_gravity_status(t)
        if gravidade is not None:
            dados["gravidade"] = gravidade

        dor_intensa = self._extract_pain_intensity_status(t)
        if dor_intensa is not None:
            dados["dor_intensa"] = dor_intensa

        toxemia = self._extract_toxemia_status(t)
        if toxemia is not None:
            dados["toxemia"] = toxemia

        prostracao = self._extract_prostration_status(t)
        if prostracao is not None:
            dados["prostracao"] = prostracao

        if self._contains_any(t, ["dor de ouvido", "dor no ouvido", "otalgia", "ouvido doendo"]):
            dados["dor_presente"] = True

        if self._contains_any(t, ["sem dor no ouvido", "sem otalgia"]):
            dados["dor_presente"] = False

        if self._contains_any(t, ["secrecao no ouvido", "otorreia", "ouvido vazando", "ouvido escorrendo", "pus no ouvido"]):
            dados["secrecao_auricular"] = True

        if self._contains_any(t, ["sem secrecao", "sem otorreia", "sem secrecao no ouvido"]):
            dados["secrecao_auricular"] = False

        if self._contains_any(t, ["dor de garganta", "odinofagia", "garganta inflamada", "garganta inflamda"]):
            dados["dor_garganta"] = True

        if self._contains_any(t, ["sem dor de garganta"]):
            dados["dor_garganta"] = False

        if self._contains_any(t, ["placas", "placa na garganta", "exsudato", "pus na amigdala", "pus nas amigdalas"]):
            dados["placas_amigdalianas"] = True

        if self._contains_any(t, ["sem placas", "sem exsudato"]):
            dados["placas_amigdalianas"] = False

        if self._contains_any(t, ["dor facial", "dor na face", "pressao na face", "seios da face"]):
            dados["dor_facial"] = True

        if self._contains_any(t, ["sem dor facial"]):
            dados["dor_facial"] = False

        if self._contains_any(t, ["secrecao nasal purulenta", "coriza purulenta", "secrecao amarela", "secrecao esverdeada"]):
            dados["secrecao_nasal_purulenta"] = True

        if self._contains_any(t, ["sem secrecao nasal", "sem coriza", "sem secrecao purulenta"]):
            dados["secrecao_nasal_purulenta"] = False

        context["dados_clinicos"] = dados
        return context

    def _extract_age(self, text: str):
        patterns = [
            r'(\d{1,3})\s*anos',
            r'idade\s*[:=]?\s*(\d{1,3})',
            r'paciente\s*de\s*(\d{1,3})\s*anos',
            r'paciente\s*com\s*(\d{1,3})\s*anos'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                idade = int(match.group(1))
                if 0 < idade < 130:
                    return idade
        return None

    def _extract_weight(self, text: str):
        patterns = [
            r'(\d{1,3})\s*kg',
            r'peso\s*[:=]?\s*(\d{1,3})',
            r'pesando\s*(\d{1,3})\s*kg'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                peso = int(match.group(1))
                if 0 < peso < 500:
                    return peso
        return None

    def _extract_duration_days(self, text: str):
        patterns = [
            r'ha\s*(\d{1,2})\s*dias',
            r'(\d{1,2})\s*dias',
            r'(\d{1,2})\s*dia'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                dias = int(match.group(1))
                if 0 <= dias <= 60:
                    return dias
        return None

    def _extract_allergy_status(self, text: str):
        if self._contains_any(text, [
            "sem alergia", "nao tem alergia", "nega alergia", "sem alergia a penicilina"
        ]):
            return False

        if self._contains_any(text, [
            "alergia", "alergico", "alergica", "alergia a penicilina"
        ]):
            return True

        return None

    def _extract_fever_status(self, text: str):
        if self._contains_any(text, [
            "sem febre", "afebril", "nega febre"
        ]):
            return False

        if self._contains_any(text, [
            "febre", "febril", "temperatura elevada"
        ]):
            return True

        return None

    def _extract_explicit_gravity_status(self, text: str):
        if self._contains_any(text, [
            "sem gravidade", "sem sinais de gravidade", "quadro leve"
        ]):
            return False

        if self._contains_any(text, [
            "com gravidade", "sinais de gravidade", "quadro grave"
        ]):
            return True

        return None

    def _extract_pain_intensity_status(self, text: str):
        if self._contains_any(text, [
            "dor intensa", "dor forte", "muita dor"
        ]):
            return True

        if self._contains_any(text, [
            "dor leve", "dor moderada", "sem dor intensa"
        ]):
            return False

        return None

    def _extract_toxemia_status(self, text: str):
        if self._contains_any(text, [
            "sem toxemia", "nega toxemia"
        ]):
            return False

        if self._contains_any(text, [
            "toxemia", "sinais de toxemia"
        ]):
            return True

        return None

    def _extract_prostration_status(self, text: str):
        if self._contains_any(text, [
            "sem prostracao", "bom estado geral", "ativo", "sem prostração"
        ]):
            return False

        if self._contains_any(text, [
            "prostrado", "prostracao", "prostração", "abatido"
        ]):
            return True

        return None

    def _build_response(self, question: str, context: dict, reasoning: dict) -> dict:
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})
        status = reasoning.get("status")

        if status == "insufficient_data":
            resposta = "Preciso entender melhor o quadro clínico para orientar a conduta."
            return {
                "resposta": resposta,
                "clinical_response": {
                    "tipo": "coleta_dados",
                    "cenario": scenario,
                    "resposta": resposta,
                    "perguntas": reasoning.get("missing", []),
                    "dados_clinicos": dados
                }
            }

        if status == "need_more_data":
            resposta = "Ainda preciso de algumas informações para definir a conduta:"
            return {
                "resposta": resposta,
                "clinical_response": {
                    "tipo": "coleta_dados",
                    "cenario": scenario,
                    "resposta": resposta,
                    "perguntas": reasoning.get("missing", []),
                    "dados_clinicos": dados
                }
            }

        if status == "ready_for_treatment":
            return self.decision_engine.decide(question=question, context=context)

        resposta = "Ainda não consegui estruturar a conduta com segurança. Preciso de mais dados clínicos."
        return {
            "resposta": resposta,
            "clinical_response": {
                "tipo": "coleta_dados",
                "cenario": scenario,
                "resposta": resposta,
                "perguntas": ["Descreva melhor o quadro clínico atual."],
                "dados_clinicos": dados
            }
        }
