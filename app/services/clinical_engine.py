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
    - interpretar respostas curtas dentro do contexto clínico atual
    - chamar o reasoning_engine para avaliar prontidão
    - chamar o decision_engine quando houver base suficiente
    - anexar confidence, risco e explicabilidade
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

    def _has_negation(self, text: str) -> bool:
        negations = [
            "sem ",
            "nao ",
            "nega ",
            "ausencia de",
            "ausente",
            "sem sinais de"
        ]
        return any(token in text for token in negations)

    def _is_short_contextual_answer(self, text: str) -> bool:
        return len(text.split()) <= 8

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
        scenario = context.get("scenario")
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

        if self._contains_any(t, [
            "secrecao nasal purulenta",
            "coriza purulenta",
            "secrecao amarela",
            "secrecao esverdeada"
        ]):
            dados["secrecao_nasal_purulenta"] = True

        if self._contains_any(t, ["sem secrecao nasal", "sem coriza", "sem secrecao purulenta"]):
            dados["secrecao_nasal_purulenta"] = False

        self._extract_contextual_shorthand(t, scenario, dados)

        context["dados_clinicos"] = dados
        return context

    def _extract_contextual_shorthand(self, text: str, scenario: str, dados: dict):
        if scenario == "otite_media_aguda":
            if self._contains_any(text, [
                "secrecao no ouvido",
                "otorreia",
                "ouvido vazando",
                "ouvido escorrendo",
                "pus no ouvido"
            ]):
                dados["secrecao_auricular"] = True

            if self._contains_any(text, [
                "sem secrecao no ouvido",
                "sem otorreia"
            ]):
                dados["secrecao_auricular"] = False

            if self._is_short_contextual_answer(text):
                if self._contains_any(text, ["secrecao", "pus"]) and not self._has_negation(text):
                    dados["secrecao_auricular"] = True
                    if self._contains_any(text, ["pus"]):
                        dados["secrecao_purulenta"] = True

                if self._contains_any(text, ["sem secrecao", "sem pus"]) or (
                    self._has_negation(text) and self._contains_any(text, ["secrecao", "pus"])
                ):
                    dados["secrecao_auricular"] = False
                    if self._contains_any(text, ["pus"]):
                        dados["secrecao_purulenta"] = False

        if scenario == "faringoamigdalite":
            if self._is_short_contextual_answer(text):
                if self._contains_any(text, ["placas", "exsudato", "pus"]) and not self._has_negation(text):
                    dados["placas_amigdalianas"] = True

                if self._contains_any(text, ["sem placas", "sem exsudato"]) or (
                    self._has_negation(text) and self._contains_any(text, ["placas", "exsudato"])
                ):
                    dados["placas_amigdalianas"] = False

        if scenario == "sinusite":
            if self._is_short_contextual_answer(text):
                if self._contains_any(text, ["secrecao", "coriza", "pus"]) and not self._has_negation(text):
                    dados["secrecao_nasal_purulenta"] = True

                if self._contains_any(text, ["sem secrecao", "sem coriza"]) or (
                    self._has_negation(text) and self._contains_any(text, ["secrecao", "coriza"])
                ):
                    dados["secrecao_nasal_purulenta"] = False

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
            r'(\d{1,3})kg',
            r'peso\s*[:=]?\s*(\d{1,3})',
            r'pesando\s*(\d{1,3})\s*kg',
            r'com\s*(\d{1,3})\s*kg',
            r'com(\d{1,3})\s*kg'
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
            "sem toxemia", "nega toxemia", "sem sinais de toxemia"
        ]):
            return False

        if self._contains_any(text, [
            "toxemia", "sinais de toxemia"
        ]):
            return True

        return None

    def _extract_prostration_status(self, text: str):
        if self._contains_any(text, [
            "sem prostracao",
            "sem prostração",
            "bom estado geral",
            "ativo"
        ]):
            return False

        if self._contains_any(text, [
            "prostrado",
            "prostracao",
            "prostração",
            "abatido",
            "paciente prostrado"
        ]):
            return True

        return None

    def _build_response(self, question: str, context: dict, reasoning: dict) -> dict:
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})
        status = reasoning.get("status")

        confidence = self._calculate_confidence(scenario, dados, reasoning)
        risk_level = self._calculate_risk_level(scenario, dados)
        explanation = self._build_explanation(scenario, dados, reasoning)

        if status == "insufficient_data":
            resposta = "Preciso entender melhor o quadro clínico para orientar a conduta."
            return {
                "resposta": resposta,
                "clinical_response": {
                    "tipo": "coleta_dados",
                    "cenario": scenario,
                    "resposta": resposta,
                    "perguntas": reasoning.get("missing", []),
                    "dados_clinicos": dados,
                    "confidence": confidence,
                    "risk_level": risk_level,
                    "explanation": explanation
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
                    "dados_clinicos": dados,
                    "confidence": confidence,
                    "risk_level": risk_level,
                    "explanation": explanation
                }
            }

        if status == "ready_for_treatment":
            response = self.decision_engine.decide(question=question, context=context)

            clinical_response = response.get("clinical_response", {})
            clinical_response["confidence"] = confidence
            clinical_response["risk_level"] = risk_level
            clinical_response["explanation"] = explanation
            clinical_response["missing_relevant_data"] = self._relevant_missing_data(scenario, dados)

            response["clinical_response"] = clinical_response
            return response

        resposta = "Ainda não consegui estruturar a conduta com segurança. Preciso de mais dados clínicos."
        return {
            "resposta": resposta,
            "clinical_response": {
                "tipo": "coleta_dados",
                "cenario": scenario,
                "resposta": resposta,
                "perguntas": ["Descreva melhor o quadro clínico atual."],
                "dados_clinicos": dados,
                "confidence": confidence,
                "risk_level": risk_level,
                "explanation": explanation
            }
        }

    def _calculate_confidence(self, scenario: str, dados: dict, reasoning: dict) -> str:
        status = reasoning.get("status")

        if status in ["insufficient_data", "need_more_data"]:
            known_fields = sum(1 for v in dados.values() if v is not None)
            if known_fields <= 2:
                return "baixa"
            if known_fields <= 5:
                return "moderada"
            return "moderada"

        strong_markers = 0
        uncertain_markers = 0

        if scenario == "otite_media_aguda":
            if dados.get("dor_presente") is True:
                strong_markers += 1
            if dados.get("febre") is True:
                strong_markers += 1
            if dados.get("secrecao_auricular") is True:
                strong_markers += 1
            if dados.get("dor_intensa") is True:
                strong_markers += 1
            if dados.get("dor_intensa") is None:
                uncertain_markers += 1
            if dados.get("toxemia") is None:
                uncertain_markers += 1
            if dados.get("prostracao") is None:
                uncertain_markers += 1

        elif scenario == "faringoamigdalite":
            if dados.get("dor_garganta") is True:
                strong_markers += 1
            if dados.get("febre") is True:
                strong_markers += 1
            if dados.get("placas_amigdalianas") is True:
                strong_markers += 1
            if dados.get("toxemia") is None:
                uncertain_markers += 1
            if dados.get("prostracao") is None:
                uncertain_markers += 1

        elif scenario == "sinusite":
            if dados.get("dor_facial") is True:
                strong_markers += 1
            if dados.get("secrecao_nasal_purulenta") is True:
                strong_markers += 1
            if dados.get("duracao_dias") is not None and dados.get("duracao_dias") >= 10:
                strong_markers += 1
            if dados.get("febre") is True:
                strong_markers += 1
            if dados.get("toxemia") is None:
                uncertain_markers += 1
            if dados.get("prostracao") is None:
                uncertain_markers += 1

        if strong_markers >= 3 and uncertain_markers == 0:
            return "alta"
        if strong_markers >= 2:
            return "moderada"
        return "baixa"

    def _calculate_risk_level(self, scenario: str, dados: dict) -> str:
        if dados.get("toxemia") is True or dados.get("prostracao") is True:
            return "alto"

        if dados.get("dor_intensa") is True or dados.get("gravidade") is True:
            return "moderado"

        if scenario == "sinusite" and dados.get("febre") is True and dados.get("duracao_dias") is not None and dados.get("duracao_dias") >= 10:
            return "moderado"

        return "baixo"

    def _build_explanation(self, scenario: str, dados: dict, reasoning: dict) -> str:
        status = reasoning.get("status")

        if scenario == "otite_media_aguda":
            reasons = []
            if dados.get("dor_presente") is True:
                reasons.append("há otalgia")
            if dados.get("febre") is True:
                reasons.append("há febre")
            if dados.get("secrecao_auricular") is True:
                reasons.append("há secreção auricular")
            if dados.get("dor_intensa") is True:
                reasons.append("há dor intensa")
            if dados.get("alergia") is True:
                reasons.append("há alergia à penicilina")

            if status == "ready_for_treatment":
                return self._join_explanation(
                    "A decisão clínica foi apoiada porque",
                    reasons,
                    "o conjunto aumenta a plausibilidade de otite média aguda com necessidade de conduta ativa."
                )

            return self._join_explanation(
                "Ainda faltam elementos para uma decisão final porque",
                reasons,
                "o caso ainda precisa de melhor definição clínica."
            )

        if scenario == "faringoamigdalite":
            reasons = []
            if dados.get("dor_garganta") is True:
                reasons.append("há dor de garganta")
            if dados.get("febre") is True:
                reasons.append("há febre")
            if dados.get("placas_amigdalianas") is True:
                reasons.append("há placas ou exsudato")
            if dados.get("alergia") is True:
                reasons.append("há alergia à penicilina")

            if status == "ready_for_treatment":
                return self._join_explanation(
                    "A decisão clínica foi apoiada porque",
                    reasons,
                    "o conjunto aumenta a plausibilidade de infecção bacteriana de garganta."
                )

            return self._join_explanation(
                "Ainda faltam elementos para uma decisão final porque",
                reasons,
                "o quadro ainda precisa de melhor definição etiológica."
            )

        if scenario == "sinusite":
            reasons = []
            if dados.get("dor_facial") is True:
                reasons.append("há dor facial")
            if dados.get("secrecao_nasal_purulenta") is True:
                reasons.append("há secreção nasal purulenta")
            if dados.get("duracao_dias") is not None:
                reasons.append(f"há {dados.get('duracao_dias')} dias de evolução")
            if dados.get("febre") is True:
                reasons.append("há febre")

            if status == "ready_for_treatment":
                return self._join_explanation(
                    "A decisão clínica foi apoiada porque",
                    reasons,
                    "esses elementos ajudam a diferenciar quadro bacteriano de quadro viral."
                )

            return self._join_explanation(
                "Ainda faltam elementos para uma decisão final porque",
                reasons,
                "a evolução clínica ainda precisa ser melhor caracterizada."
            )

        return "A resposta foi construída com base nos dados clínicos disponíveis até o momento."

    def _join_explanation(self, intro: str, reasons: list[str], ending: str) -> str:
        if not reasons:
            return f"{intro} ainda há poucos dados clínicos disponíveis, e {ending}"
        return f"{intro} " + ", ".join(reasons) + f", e {ending}"

    def _relevant_missing_data(self, scenario: str, dados: dict) -> list[str]:
        missing = []

        if scenario == "otite_media_aguda":
            if dados.get("dor_intensa") is None:
                missing.append("intensidade da dor")
            if dados.get("toxemia") is None:
                missing.append("toxemia")
            if dados.get("prostracao") is None:
                missing.append("prostração")

        elif scenario == "faringoamigdalite":
            if dados.get("toxemia") is None:
                missing.append("toxemia")
            if dados.get("prostracao") is None:
                missing.append("prostração")

        elif scenario == "sinusite":
            if dados.get("febre") is None:
                missing.append("febre")
            if dados.get("toxemia") is None:
                missing.append("toxemia")
            if dados.get("prostracao") is None:
                missing.append("prostração")

        return missing
