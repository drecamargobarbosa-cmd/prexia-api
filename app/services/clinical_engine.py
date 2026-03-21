import re
from copy import deepcopy
from app.services.protocol_engine import ProtocolEngine


class ClinicalEngine:
    """
    Motor clínico stateless.

    Objetivos:
    - acumular dados clínicos a partir do contexto recebido
    - interpretar respostas curtas e fragmentadas
    - reconhecer afirmações e negações clínicas
    - separar dor presente de dor intensa
    - evitar loop de perguntas repetidas
    - reconhecer intenção clínica:
      tratamento, antibiótico, medicamento e dose
    - ampliar coleta clínica antes de sugerir antibiótico
    - interpretar melhor respostas parciais e frases compostas
    """

    def __init__(self):
        self.protocol_engine = ProtocolEngine()

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

        response = self._build_response(merged_context)

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
            "á": "a",
            "à": "a",
            "ã": "a",
            "â": "a",
            "é": "e",
            "ê": "e",
            "í": "i",
            "ó": "o",
            "ô": "o",
            "õ": "o",
            "ú": "u",
            "ç": "c"
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _contains_expression(self, text: str, expression: str) -> bool:
        pattern = r'(^|[\s,;:.!?()])' + re.escape(expression) + r'($|[\s,;:.!?()])'
        return re.search(pattern, text) is not None

    def _contains_any_expression(self, text: str, expressions: list[str]) -> bool:
        return any(self._contains_expression(text, exp) for exp in expressions)

    def _contains_any_token(self, text: str, tokens: list[str]) -> bool:
        return any(token in text for token in tokens)

    def _has_any_negation(self, text: str) -> bool:
        neg_tokens = [
            "sem ",
            "nao ",
            "nega ",
            "ausencia de",
            "ausente"
        ]
        return any(token in text for token in neg_tokens)

    def _mentions_ear_pain(self, text: str) -> bool:
        direct_terms = [
            "dor de ouvido",
            "dor no ouvido",
            "ouvido doendo",
            "otalgia",
            "ouvido inflamado",
            "or de ouvido"
        ]

        if any(term in text for term in direct_terms):
            return True

        if "ouvido" in text and any(term in text for term in ["dor", "doendo", "otalgia"]):
            return True

        return False

    def _detect_scenario(self, text: str):
        t = self._normalize(text)

        if self._mentions_ear_pain(t) or "otite" in t:
            return "otite_media_aguda"

        if any(term in t for term in [
            "sinusite",
            "dor na face",
            "seios da face",
            "dor facial"
        ]):
            return "sinusite"

        if any(term in t for term in [
            "dor de garganta",
            "amigdalite",
            "faringite",
            "faringoamigdalite"
        ]):
            return "faringoamigdalite"

        return None

    def _detect_intent(self, text: str):
        t = self._normalize(text)

        antibiotic_terms = [
            "qual antibiotico",
            "qual o antibiotico",
            "qual seria o antibiotico",
            "antibiotico indicado",
            "antibiotico",
            "antibiotico de escolha"
        ]

        medication_terms = [
            "qual o medicamento",
            "qual medicamento",
            "qual seria o medicamento",
            "qual remedio",
            "qual o remedio",
            "qual seria o remedio",
            "medicamento indicado",
            "remedio indicado"
        ]

        dose_terms = [
            "qual a dose",
            "qual dose",
            "qual a dose do antibiotico",
            "qual dose do antibiotico",
            "qual a dose de antibiotico",
            "qual dose de antibiotico",
            "dose do antibiotico",
            "dose de antibiotico",
            "dosagem",
            "posologia",
            "quanto mg",
            "qual a posologia",
            "qual posologia"
        ]

        treatment_terms = [
            "qual o tratamento",
            "qual tratamento",
            "qual seria o tratamento",
            "como tratar",
            "tratamento",
            "qual a conduta",
            "qual conduta",
            "conduta"
        ]

        if any(term in t for term in dose_terms):
            return "dose"

        if any(term in t for term in medication_terms):
            return "medicamento"

        if any(term in t for term in antibiotic_terms):
            return "antibiotico"

        if any(term in t for term in treatment_terms):
            return "tratamento"

        return "geral"

    def _extract_and_update_clinical_data(self, text: str, context: dict) -> dict:
        dados = context["dados_clinicos"]
        t = self._normalize(text)

        alergia = self._extract_allergy_status(t)
        if alergia is not None:
            dados["alergia"] = alergia

        febre = self._extract_fever_status(t)
        if febre is not None:
            dados["febre"] = febre
            if febre is False:
                dados["febre_alta"] = False

        febre_alta = self._extract_high_fever_status(t, dados)
        if febre_alta is not None:
            dados["febre_alta"] = febre_alta
            if febre_alta is True:
                dados["febre"] = True

        dor_presente = self._extract_pain_presence_status(t)
        if dor_presente is not None:
            dados["dor_presente"] = dor_presente

        dor_intensa = self._extract_pain_intensity_status(t)
        if dor_intensa is not None:
            dados["dor_intensa"] = dor_intensa
            if dor_intensa is True:
                dados["dor_presente"] = True

        toxemia = self._extract_toxemia_status(t)
        if toxemia is not None:
            dados["toxemia"] = toxemia

        prostracao = self._extract_prostration_status(t)
        if prostracao is not None:
            dados["prostracao"] = prostracao

        secrecao_auricular = self._extract_ear_discharge_status(t)
        if secrecao_auricular is not None:
            dados["secrecao_auricular"] = secrecao_auricular

        secrecao_purulenta = self._extract_purulent_discharge_status(t)
        if secrecao_purulenta is not None:
            dados["secrecao_purulenta"] = secrecao_purulenta
            if secrecao_purulenta is True:
                dados["secrecao_auricular"] = True

        duracao_dias = self._extract_duration_days(t)
        if duracao_dias is not None:
            dados["duracao_dias"] = duracao_dias

        idade = self._extract_age(t)
        if idade is not None:
            dados["idade"] = idade

        peso = self._extract_weight(t)
        if peso is not None:
            dados["peso"] = peso

        inferred = self._infer_gravity_from_signs(dados)
        if inferred is not None:
            dados["gravidade"] = inferred

        explicit_gravity = self._extract_explicit_gravity_status(t)
        if explicit_gravity is not None:
            dados["gravidade"] = explicit_gravity

        context["dados_clinicos"] = dados
        return context

    def _extract_allergy_status(self, text: str):
        negative_terms = [
            "sem alergia",
            "sem alergias",
            "nao tem alergia",
            "nao possui alergia",
            "nega alergia",
            "nega alergias",
            "sem alergia a penicilina",
            "sem alergia a antibiotico",
            "sem alergia medicamentosa"
        ]

        positive_terms = [
            "com alergia",
            "com alergias",
            "tem alergia",
            "tem alergias",
            "possui alergia",
            "possui alergias",
            "alergia a penicilina",
            "alergico a penicilina",
            "alergica a penicilina",
            "alergia medicamentosa",
            "alergico",
            "alergica"
        ]

        if self._contains_any_expression(text, negative_terms):
            return False

        if self._contains_any_expression(text, positive_terms):
            return True

        return None

    def _extract_fever_status(self, text: str):
        negative_terms = [
            "sem febre",
            "afebril",
            "nega febre",
            "nao tem febre",
            "nao apresenta febre",
            "ausencia de febre"
        ]

        positive_terms = [
            "com febre",
            "tem febre",
            "apresenta febre",
            "febril",
            "temperatura elevada",
            "paciente com febre",
            "febre,"
        ]

        if self._contains_any_expression(text, negative_terms):
            return False

        if "febre alta" in text:
            return True

        if self._contains_any_expression(text, positive_terms) or " febre" in text or text.startswith("febre"):
            return True

        return None

    def _extract_high_fever_status(self, text: str, dados: dict):
        if dados.get("febre") is False:
            return False

        negative_terms = [
            "sem febre alta",
            "nega febre alta",
            "nao tem febre alta",
            "febre nao e alta",
            "a febre nao e alta",
            "febre baixa"
        ]

        positive_terms = [
            "febre alta",
            "temperatura alta",
            "temperatura muito alta",
            "a febre e alta"
        ]

        if self._contains_any_expression(text, negative_terms):
            return False

        if self._contains_any_expression(text, positive_terms):
            return True

        if text in ["alta", "muito alta"] and dados.get("febre") is True:
            return True

        return None

    def _extract_pain_presence_status(self, text: str):
        negative_terms = [
            "sem dor",
            "nega dor",
            "nao tem dor",
            "nao apresenta dor"
        ]

        positive_terms = [
            "tem dor",
            "com dor",
            "apresenta dor",
            "dor de ouvido",
            "dor no ouvido",
            "or de ouvido",
            "ouvido doendo",
            "otalgia",
            "paciente com dor",
            "dor,"
        ]

        if self._contains_any_expression(text, negative_terms):
            return False

        if self._contains_any_expression(text, positive_terms) or text.startswith("dor") or self._mentions_ear_pain(text):
            return True

        return None

    def _extract_pain_intensity_status(self, text: str):
        negative_terms = [
            "sem dor intensa",
            "dor leve",
            "dor media",
            "dor media a moderada",
            "dor moderada",
            "dor media/moderada",
            "dor suportavel",
            "dor toleravel",
            "nao e dor intensa",
            "a dor nao e intensa"
        ]

        positive_terms = [
            "dor intensa",
            "muita dor",
            "dor forte",
            "otalgia intensa",
            "dor importante",
            "dor muito forte",
            "com dor intensa"
        ]

        if self._contains_any_expression(text, negative_terms):
            return False

        if self._contains_any_expression(text, positive_terms):
            return True

        return None

    def _extract_toxemia_status(self, text: str):
        negative_terms = [
            "sem toxemia",
            "nega toxemia",
            "nao apresenta toxemia",
            "sem sinais de toxemia",
            "sem sinais toxicos",
            "sem sinais toxicos"
        ]

        positive_terms = [
            "tem toxemia",
            "com toxemia",
            "apresenta toxemia",
            "toxemia",
            "toxico",
            "toxemico",
            "sinais de toxemia"
        ]

        if self._contains_any_expression(text, negative_terms):
            return False

        if self._contains_any_expression(text, positive_terms):
            return True

        return None

    def _extract_prostration_status(self, text: str):
        negative_terms = [
            "sem prostracao",
            "sem prostacao",
            "nega prostracao",
            "nega prostacao",
            "nao prostrado",
            "nao prostado",
            "nao esta prostrado",
            "nao esta prostado",
            "paciente nao esta prostrado",
            "paciente nao esta prostado",
            "ativo",
            "bom estado geral"
        ]

        positive_terms = [
            "tem prostracao",
            "tem prostacao",
            "com prostracao",
            "com prostacao",
            "apresenta prostracao",
            "apresenta prostacao",
            "prostrado",
            "prostado",
            "prostracao",
            "prostacao",
            "abatido importante",
            "estado geral ruim",
            "paciente prostrado"
        ]

        if self._contains_any_expression(text, negative_terms):
            return False

        if self._contains_any_expression(text, positive_terms):
            return True

        return None

    def _extract_ear_discharge_status(self, text: str):
        negative_terms = [
            "sem secrecao no ouvido",
            "sem secrecao auricular",
            "sem otorreia",
            "sem otorria",
            "nega secrecao no ouvido",
            "nega secrecao auricular",
            "nao tem secrecao no ouvido",
            "nao apresenta secrecao no ouvido",
            "ouvido seco",
            "sem secrecao",
            "sem saida de secrecao"
        ]

        positive_terms = [
            "secrecao no ouvido",
            "secrecao auricular",
            "otorreia",
            "otorria",
            "sai secrecao do ouvido",
            "ouvido vazando",
            "ouvido escorrendo",
            "com secrecao",
            "existe secrecao",
            "paciente com secrecao",
            "saida de secrecao",
            "secrecao"
        ]

        if self._contains_any_expression(text, negative_terms):
            return False

        if self._contains_any_expression(text, positive_terms):
            return True

        if "secrecao" in text and not self._has_any_negation(text):
            return True

        return None

    def _extract_purulent_discharge_status(self, text: str):
        negative_terms = [
            "sem secrecao purulenta",
            "sem pus",
            "nega pus",
            "nao tem pus"
        ]

        positive_terms = [
            "secrecao purulenta",
            "pus",
            "secrecao com pus",
            "saida de pus",
            "otorreia purulenta"
        ]

        if self._contains_any_expression(text, negative_terms):
            return False

        if self._contains_any_expression(text, positive_terms):
            return True

        return None

    def _extract_explicit_gravity_status(self, text: str):
        negative_terms = [
            "sem gravidade",
            "sem sinais de gravidade",
            "nega gravidade",
            "nao tem gravidade",
            "quadro leve",
            "sem sinais de alarme"
        ]

        positive_terms = [
            "tem gravidade",
            "com gravidade",
            "apresenta gravidade",
            "sinais de gravidade",
            "quadro grave"
        ]

        if self._contains_any_expression(text, negative_terms):
            return False

        if self._contains_any_expression(text, positive_terms):
            return True

        return None

    def _infer_gravity_from_signs(self, dados: dict):
        severe_signs = [
            dados.get("febre_alta"),
            dados.get("dor_intensa"),
            dados.get("toxemia"),
            dados.get("prostracao")
        ]

        if any(value is True for value in severe_signs):
            return True

        known = [value for value in severe_signs if value is not None]
        if len(known) == 4 and all(value is False for value in known):
            return False

        return None

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
                try:
                    idade = int(match.group(1))
                    if 0 < idade < 130:
                        return idade
                except ValueError:
                    pass

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
                try:
                    peso = int(match.group(1))
                    if 0 < peso < 500:
                        return peso
                except ValueError:
                    pass

        return None

    def _extract_duration_days(self, text: str):
        direct_patterns = [
            r'ha\s*(\d{1,2})\s*dias',
            r'(\d{1,2})\s*dias\s*de\s*sintomas?',
            r'(\d{1,2})\s*dias\s*de\s*dor',
            r'comecou\s*ha\s*(\d{1,2})\s*dias',
            r'inicio\s*ha\s*(\d{1,2})\s*dias',
            r'sintomas?\s*ha\s*(\d{1,2})\s*dias',
            r'(\d{1,2})\s*dias\s*de\s*evolucao',
            r'^(\d{1,2})\s*dias$',
            r'^(\d{1,2})\s*dia$',
            r'(\d{1,2})\s*dias\b',
            r'(\d{1,2})\s*dia\b'
        ]

        for pattern in direct_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    dias = int(match.group(1))
                    if 0 <= dias <= 60:
                        return dias
                except ValueError:
                    pass

        typo_text = text.replace(" dis ", " dias ")
        typo_text = re.sub(r'\b(\d{1,2})\s*dis\b', r'\1 dias', typo_text)
        typo_text = typo_text.replace(" de sintoma", " de sintomas")

        typo_patterns = [
            r'(\d{1,2})\s*dias\s*de\s*sintomas?',
            r'^(\d{1,2})\s*dias$',
            r'(\d{1,2})\s*dias\b'
        ]

        for pattern in typo_patterns:
            match = re.search(pattern, typo_text)
            if match:
                try:
                    dias = int(match.group(1))
                    if 0 <= dias <= 60:
                        return dias
                except ValueError:
                    pass

        if self._contains_expression(text, "hoje"):
            return 0

        return None

    def _format_boolean_label(self, value, true_label="Sim", false_label="Não", unknown_label="Não informado"):
        if value is True:
            return true_label
        if value is False:
            return false_label
        return unknown_label

    def _otitis_summary(self, dados: dict) -> str:
        parts = []

        idade = dados.get("idade")
        if idade is not None:
            parts.append(f"Paciente com {idade} anos")

        if dados.get("dor_presente") is True:
            parts.append("otalgia presente")

        duracao_dias = dados.get("duracao_dias")
        if duracao_dias is not None:
            if duracao_dias == 1:
                parts.append("1 dia de evolução")
            else:
                parts.append(f"{duracao_dias} dias de evolução")

        parts.append(f"febre: {self._format_boolean_label(dados.get('febre'))}")
        parts.append(f"secreção auricular: {self._format_boolean_label(dados.get('secrecao_auricular'))}")
        parts.append(f"dor intensa: {self._format_boolean_label(dados.get('dor_intensa'))}")
        parts.append(f"toxemia: {self._format_boolean_label(dados.get('toxemia'))}")
        parts.append(f"prostração: {self._format_boolean_label(dados.get('prostracao'))}")
        parts.append(f"alergia à penicilina: {self._format_boolean_label(dados.get('alergia'))}")
        parts.append(f"sinais de gravidade: {self._format_boolean_label(dados.get('gravidade'))}")

        return "; ".join(parts) + "."

    def _build_structured_text(
        self,
        avaliacao_clinica: str,
        diagnostico_provavel: str,
        conduta_recomendada: str,
        justificativa: str = "",
        observacoes_clinicas: str = "",
        medicacao: str = "",
        dose: str = "",
        posologia: str = "",
        duracao: str = ""
    ) -> str:
        sections = [
            f"Avaliação clínica: {avaliacao_clinica}",
            f"Diagnóstico provável: {diagnostico_provavel}",
            f"Conduta recomendada: {conduta_recomendada}"
        ]

        if medicacao:
            sections.append(f"Medicação: {medicacao}")

        if dose:
            sections.append(f"Dose: {dose}")

        if posologia:
            sections.append(f"Posologia: {posologia}")

        if duracao:
            sections.append(f"Duração: {duracao}")

        if justificativa:
            sections.append(f"Justificativa: {justificativa}")

        if observacoes_clinicas:
            sections.append(f"Observações clínicas: {observacoes_clinicas}")

        return "\n\n".join(sections)

    def _build_response(self, context: dict) -> dict:
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})
        intent = context.get("intent", "geral")

        if not scenario:
            resposta = "Preciso entender melhor o quadro clínico para orientar a conduta."
            return {
                "resposta": resposta,
                "clinical_response": {
                    "tipo": "coleta_dados",
                    "cenario": None,
                    "resposta": resposta,
                    "perguntas": [
                        "Qual é a hipótese clínica principal?",
                        "Qual é a idade do paciente?",
                        "Há alergia medicamentosa?",
                        "Há sinais de gravidade?"
                    ],
                    "dados_clinicos": dados
                },
                "history": context.get("history", []),
                "context": context
            }

        missing_questions = self._get_missing_questions(scenario, dados)

        if missing_questions:
            resposta = "Ainda preciso de algumas informações para definir o tratamento:"
            return {
                "resposta": resposta,
                "clinical_response": {
                    "tipo": "coleta_dados",
                    "cenario": scenario,
                    "resposta": resposta,
                    "perguntas": missing_questions,
                    "dados_clinicos": dados
                },
                "history": context.get("history", []),
                "context": context
            }

        if scenario == "otite_media_aguda":
            if self._has_minimum_diagnostic_support_for_otitis(dados):
                if intent in ["tratamento", "antibiotico", "medicamento", "dose", "geral"]:
                    return self._generate_complete_otitis_therapeutic_response(context)

                protocol_result = self._generate_protocol_response(scenario, dados)

                return {
                    "resposta": protocol_result["resposta"],
                    "clinical_response": {
                        "tipo": "conduta",
                        "cenario": scenario,
                        "resposta": protocol_result["resposta"],
                        "conduta": protocol_result.get("conduta"),
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

            if self._has_sufficient_otitis_assessment_for_observation(dados):
                return self._generate_non_antibiotic_otitis_response(context)

            resposta = (
                "Ainda não há elementos clínicos suficientes para sustentar indicação de antibiótico com segurança. "
                "Preciso consolidar melhor os sinais e sintomas do quadro de otite antes de avançar na escolha do medicamento."
            )
            return {
                "resposta": resposta,
                "clinical_response": {
                    "tipo": "coleta_dados",
                    "cenario": scenario,
                    "resposta": resposta,
                    "perguntas": self._get_diagnostic_support_questions_for_otitis(dados),
                    "dados_clinicos": dados
                },
                "history": context.get("history", []),
                "context": context
            }

        if intent == "tratamento":
            return self._generate_treatment_response(context)

        if intent == "antibiotico":
            return self._generate_antibiotic_response(context)

        if intent == "medicamento":
            return self._generate_medication_response(context)

        if intent == "dose":
            return self._generate_dose_response(context)

        protocol_result = self._generate_protocol_response(scenario, dados)

        return {
            "resposta": protocol_result["resposta"],
            "clinical_response": {
                "tipo": "conduta",
                "cenario": scenario,
                "resposta": protocol_result["resposta"],
                "conduta": protocol_result.get("conduta"),
                "dados_clinicos": dados
            },
            "history": context.get("history", []),
            "context": context
        }

    def _get_missing_questions(self, scenario: str, dados: dict):
        questions = []

        if scenario == "otite_media_aguda":
            if dados.get("febre") is None:
                questions.append("Há febre no quadro?")

            if dados.get("secrecao_auricular") is None:
                questions.append("Há secreção no ouvido ou otorreia?")

            if dados.get("duracao_dias") is None:
                questions.append("Há quantos dias os sintomas começaram?")

            if dados.get("febre") is True and dados.get("febre_alta") is None:
                questions.append("A febre é alta?")

            if dados.get("toxemia") is None:
                questions.append("Há sinais de toxemia?")

            if dados.get("prostracao") is None:
                questions.append("O paciente apresenta prostração?")

            if dados.get("alergia") is None:
                questions.append("O paciente tem alergia à penicilina?")

            if dados.get("idade") is None:
                questions.append("Qual é a idade do paciente?")

            idade = dados.get("idade")
            if idade is not None and idade < 12 and dados.get("peso") is None:
                questions.append("Qual é o peso do paciente em kg?")

            return questions

        if dados.get("gravidade") is None:
            if dados.get("febre_alta") is None and dados.get("febre") is not False:
                questions.append("A febre é alta?")
            if dados.get("dor_intensa") is None:
                questions.append("A dor é intensa?")
            if dados.get("toxemia") is None:
                questions.append("Há sinais de toxemia?")
            if dados.get("prostracao") is None:
                questions.append("O paciente apresenta prostração?")

        if dados.get("alergia") is None:
            questions.append("O paciente tem alergia à penicilina?")

        if dados.get("idade") is None:
            questions.append("Qual é a idade do paciente?")

        idade = dados.get("idade")
        if idade is not None and idade < 12 and dados.get("peso") is None:
            questions.append("Qual é o peso do paciente em kg?")

        return questions

    def _get_diagnostic_support_questions_for_otitis(self, dados: dict):
        questions = []

        if dados.get("febre") is None:
            questions.append("Há febre associada ao quadro?")

        if dados.get("secrecao_auricular") is None:
            questions.append("Há secreção no ouvido ou saída de secreção?")

        if dados.get("duracao_dias") is None:
            questions.append("Há quantos dias os sintomas começaram?")

        if dados.get("dor_intensa") is None:
            questions.append("A dor é intensa?")

        return questions

    def _has_minimum_diagnostic_support_for_otitis(self, dados: dict) -> bool:
        dor_presente = dados.get("dor_presente")
        febre = dados.get("febre")
        secrecao_auricular = dados.get("secrecao_auricular")
        secrecao_purulenta = dados.get("secrecao_purulenta")
        duracao_dias = dados.get("duracao_dias")

        if dor_presente is not True:
            return False

        if duracao_dias is None:
            return False

        supporting_features = [
            febre is True,
            secrecao_auricular is True,
            secrecao_purulenta is True,
            dados.get("dor_intensa") is True
        ]

        return any(supporting_features)

    def _has_sufficient_otitis_assessment_for_observation(self, dados: dict) -> bool:
        required_fields = [
            "dor_presente",
            "duracao_dias",
            "febre",
            "secrecao_auricular",
            "dor_intensa",
            "toxemia",
            "prostracao",
            "alergia",
            "idade"
        ]

        for field in required_fields:
            if dados.get(field) is None:
                return False

        return dados.get("dor_presente") is True

    def _resolve_otitis_therapeutic_plan(self, dados: dict) -> dict:
        idade = dados.get("idade")
        peso = dados.get("peso")
        alergia = dados.get("alergia")
        gravidade = dados.get("gravidade")

        if alergia is True:
            return {
                "medicacao": "Azitromicina",
                "dose": "500 mg" if idade is not None and idade >= 12 else "10 mg/kg/dia",
                "posologia": "1 vez ao dia",
                "duracao": "5 dias",
                "justificativa_plano": (
                    "Há suporte clínico para tratamento antimicrobiano e, devido à alergia à penicilina, "
                    "foi priorizada alternativa terapêutica."
                )
            }

        if idade is not None and idade >= 12:
            if gravidade is True:
                return {
                    "medicacao": "Amoxicilina + Clavulanato",
                    "dose": "875/125 mg",
                    "posologia": "12/12 horas",
                    "duracao": "7 a 10 dias",
                    "justificativa_plano": (
                        "Em adulto com quadro compatível com otite média aguda e sinais de gravidade, "
                        "optou-se por ampliar cobertura com associação de clavulanato."
                    )
                }

            return {
                "medicacao": "Amoxicilina",
                "dose": "500 mg",
                "posologia": "8/8 horas",
                "duracao": "7 dias",
                "justificativa_plano": (
                    "Em adulto sem alergia à penicilina e sem sinais de gravidade, "
                    "a amoxicilina permanece como primeira escolha."
                )
            }

        if peso is not None:
            if gravidade is True:
                return {
                    "medicacao": "Amoxicilina + Clavulanato",
                    "dose": "80 a 90 mg/kg/dia (componente amoxicilina)",
                    "posologia": "dividida em 2 tomadas ao dia",
                    "duracao": "10 dias",
                    "justificativa_plano": (
                        "Em pediatria com sinais de gravidade, pode-se considerar ampliação de cobertura."
                    )
                }

            return {
                "medicacao": "Amoxicilina",
                "dose": "50 mg/kg/dia",
                "posologia": "dividida em 2 a 3 tomadas ao dia",
                "duracao": "7 a 10 dias",
                "justificativa_plano": (
                    "Em paciente pediátrico sem gravidade, a amoxicilina isolada é adequada."
                )
            }

        return {
            "medicacao": "Amoxicilina",
            "dose": "Seguir protocolo institucional conforme faixa etária",
            "posologia": "Conforme protocolo institucional",
            "duracao": "7 dias",
            "justificativa_plano": (
                "Há indicação clínica, porém faltam elementos adicionais para detalhar melhor a posologia."
            )
        }

    def _generate_complete_otitis_therapeutic_response(self, context: dict):
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})

        if not self._has_minimum_diagnostic_support_for_otitis(dados):
            if self._has_sufficient_otitis_assessment_for_observation(dados):
                return self._generate_non_antibiotic_otitis_response(context)

            resposta = (
                "Ainda não há base clínica suficiente para definir tratamento antimicrobiano completo com segurança. "
                "Preciso confirmar melhor febre, secreção auricular, intensidade da dor e tempo de evolução."
            )
            return {
                "resposta": resposta,
                "clinical_response": {
                    "tipo": "coleta_dados",
                    "cenario": scenario,
                    "resposta": resposta,
                    "dados_clinicos": dados
                },
                "history": context.get("history", []),
                "context": context
            }

        avaliacao = self._otitis_summary(dados)

        if dados.get("gravidade") is True:
            diagnostico = "Quadro compatível com otite média aguda com sinais de gravidade."
            conduta = (
                "Considerar antibioticoterapia, analgesia, seguimento mais próximo e reavaliação precoce, "
                "com maior atenção ao estado geral e à evolução clínica."
            )
        else:
            diagnostico = "Quadro compatível com otite média aguda sem sinais de gravidade."
            conduta = (
                "Indicar tratamento antimicrobiano conforme protocolo implementado, associado a analgesia e reavaliação clínica."
            )

        plano = self._resolve_otitis_therapeutic_plan(dados)

        justificativa = (
            f"{plano['justificativa_plano']} "
            "A consolidação terapêutica foi possível porque já há dados clínicos suficientes para sustentar decisão clínica nesta etapa."
        )

        observacoes = (
            "Monitorar evolução da dor, febre, secreção auricular e estado geral. "
            "Reavaliar precocemente se houver piora clínica, ausência de melhora ou surgimento de novos sinais de gravidade."
        )

        resposta = self._build_structured_text(
            avaliacao_clinica=avaliacao,
            diagnostico_provavel=diagnostico,
            conduta_recomendada=conduta,
            medicacao=plano["medicacao"],
            dose=plano["dose"],
            posologia=plano["posologia"],
            duracao=plano["duracao"],
            justificativa=justificativa,
            observacoes_clinicas=observacoes
        )

        return {
            "resposta": resposta,
            "clinical_response": {
                "tipo": "tratamento",
                "cenario": scenario,
                "resposta": resposta,
                "medicacao": plano["medicacao"],
                "dose": plano["dose"],
                "posologia": plano["posologia"],
                "duracao": plano["duracao"],
                "dados_clinicos": dados
            },
            "history": context.get("history", []),
            "context": context
        }

    def _generate_non_antibiotic_otitis_response(self, context: dict):
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})

        avaliacao = self._otitis_summary(dados)

        diagnostico = (
            "Quadro compatível com otalgia, sem elementos clínicos suficientes neste momento para sustentar "
            "otite média aguda bacteriana com indicação empírica de antibiótico."
        )

        conduta = (
            "Priorizar analgesia, observação clínica, confirmação diagnóstica no exame físico, especialmente com otoscopia, "
            "e reavaliação clínica se houver piora ou persistência dos sintomas."
        )

        justificativa = (
            "Até o momento, o caso não apresenta febre, secreção auricular, dor intensa, toxemia ou prostração, "
            "o que reduz o suporte clínico para antibioticoterapia empírica imediata."
        )

        observacoes = (
            "Reavaliar precocemente se surgirem febre, otorreia, piora importante da dor, comprometimento do estado geral "
            "ou outros sinais de gravidade."
        )

        resposta = self._build_structured_text(
            avaliacao_clinica=avaliacao,
            diagnostico_provavel=diagnostico,
            conduta_recomendada=conduta,
            justificativa=justificativa,
            observacoes_clinicas=observacoes
        )

        return {
            "resposta": resposta,
            "clinical_response": {
                "tipo": "reavaliacao",
                "cenario": scenario,
                "resposta": resposta,
                "dados_clinicos": dados
            },
            "history": context.get("history", []),
            "context": context
        }

    def _generate_protocol_response(self, scenario: str, dados: dict):
        try:
            protocol_response = self.protocol_engine.generate_recommendation(
                scenario=scenario,
                dados_clinicos=dados
            )

            if isinstance(protocol_response, dict):
                return protocol_response

            return {
                "resposta": str(protocol_response),
                "conduta": protocol_response
            }
        except Exception:
            return self._fallback_response(scenario, dados)

    def _generate_treatment_response(self, context: dict):
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})

        if scenario == "otite_media_aguda":
            return self._generate_complete_otitis_therapeutic_response(context)

        fallback = self._fallback_response(scenario, dados)
        return {
            "resposta": fallback["resposta"],
            "clinical_response": {
                "tipo": "tratamento",
                "cenario": scenario,
                "resposta": fallback["resposta"],
                "dados_clinicos": dados
            },
            "history": context.get("history", []),
            "context": context
        }

    def _generate_antibiotic_response(self, context: dict):
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})

        if scenario == "otite_media_aguda":
            return self._generate_complete_otitis_therapeutic_response(context)

        return {
            "resposta": "Ainda não há protocolo específico de antibiótico implementado para esse cenário.",
            "clinical_response": {
                "tipo": "antibiotico",
                "cenario": scenario,
                "dados_clinicos": dados
            },
            "history": context.get("history", []),
            "context": context
        }

    def _generate_medication_response(self, context: dict):
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})

        if scenario == "otite_media_aguda":
            return self._generate_complete_otitis_therapeutic_response(context)

        return {
            "resposta": "Ainda não há protocolo específico de medicamento implementado para esse cenário.",
            "clinical_response": {
                "tipo": "medicamento",
                "cenario": scenario,
                "dados_clinicos": dados
            },
            "history": context.get("history", []),
            "context": context
        }

    def _generate_dose_response(self, context: dict):
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})

        if scenario == "otite_media_aguda":
            return self._generate_complete_otitis_therapeutic_response(context)

        return {
            "resposta": "Ainda não há protocolo de dose específico implementado para esse cenário.",
            "clinical_response": {
                "tipo": "dose",
                "cenario": scenario,
                "dados_clinicos": dados
            },
            "history": context.get("history", []),
            "context": context
        }

    def _fallback_response(self, scenario: str, dados: dict):
        if scenario == "otite_media_aguda":
            avaliacao = self._otitis_summary(dados)

            if not self._has_minimum_diagnostic_support_for_otitis(dados):
                if self._has_sufficient_otitis_assessment_for_observation(dados):
                    resposta = self._build_structured_text(
                        avaliacao_clinica=avaliacao,
                        diagnostico_provavel=(
                            "Otalgia sem suporte clínico suficiente, neste momento, para antibioticoterapia empírica."
                        ),
                        conduta_recomendada=(
                            "Considerar manejo sintomático, observação, confirmação diagnóstica ao exame físico e reavaliação clínica."
                        ),
                        justificativa=(
                            "Os dados levantados até aqui não sustentam indicação antibiótica imediata com segurança."
                        ),
                        observacoes_clinicas=(
                            "Reavaliar se surgirem febre, secreção auricular, piora importante da dor ou comprometimento do estado geral."
                        )
                    )

                    return {
                        "resposta": resposta,
                        "conduta": {
                            "cenario": scenario,
                            "dados_clinicos": dados
                        }
                    }

                return {
                    "resposta": (
                        "Há suspeita clínica de otite, mas os dados ainda são insuficientes para sustentar indicação antibiótica com segurança. "
                        "É necessário consolidar melhor sinais e sintomas do quadro."
                    ),
                    "conduta": {
                        "cenario": scenario,
                        "dados_clinicos": dados
                    }
                }

            if dados.get("gravidade") is False and dados.get("alergia") is False:
                plano = self._resolve_otitis_therapeutic_plan(dados)
                resposta = self._build_structured_text(
                    avaliacao_clinica=avaliacao,
                    diagnostico_provavel="Quadro compatível com otite média aguda sem sinais de gravidade.",
                    conduta_recomendada=(
                        "Considerar antibioticoterapia conforme protocolo institucional, além de analgesia e reavaliação clínica."
                    ),
                    medicacao=plano["medicacao"],
                    dose=plano["dose"],
                    posologia=plano["posologia"],
                    duracao=plano["duracao"],
                    justificativa=(
                        "O conjunto de informações clínicas é compatível com o cenário de otite média aguda já implementado."
                    ),
                    observacoes_clinicas=(
                        "Reavaliar se não houver melhora clínica ou se surgirem novos sinais de gravidade."
                    )
                )

                return {
                    "resposta": resposta,
                    "conduta": {
                        "cenario": scenario,
                        "gravidade": dados.get("gravidade"),
                        "alergia": dados.get("alergia"),
                        "idade": dados.get("idade"),
                        "peso": dados.get("peso"),
                        "febre": dados.get("febre"),
                        "febre_alta": dados.get("febre_alta"),
                        "dor_presente": dados.get("dor_presente"),
                        "dor_intensa": dados.get("dor_intensa"),
                        "toxemia": dados.get("toxemia"),
                        "prostracao": dados.get("prostracao"),
                        "secrecao_auricular": dados.get("secrecao_auricular"),
                        "secrecao_purulenta": dados.get("secrecao_purulenta"),
                        "duracao_dias": dados.get("duracao_dias")
                    }
                }

            if dados.get("gravidade") is True and dados.get("alergia") is False:
                plano = self._resolve_otitis_therapeutic_plan(dados)
                resposta = self._build_structured_text(
                    avaliacao_clinica=avaliacao,
                    diagnostico_provavel="Quadro compatível com otite média aguda com sinais de gravidade.",
                    conduta_recomendada=(
                        "Avaliar com maior cautela, considerar antibioticoterapia conforme protocolo institucional e reavaliação precoce."
                    ),
                    medicacao=plano["medicacao"],
                    dose=plano["dose"],
                    posologia=plano["posologia"],
                    duracao=plano["duracao"],
                    justificativa=(
                        "A gravidade do quadro exige decisão clínica mais cuidadosa e acompanhamento mais próximo."
                    ),
                    observacoes_clinicas=(
                        "Monitorar estado geral, dor, febre e necessidade de retorno precoce."
                    )
                )

                return {
                    "resposta": resposta,
                    "conduta": {
                        "cenario": scenario,
                        "gravidade": True,
                        "alergia": False,
                        "idade": dados.get("idade"),
                        "peso": dados.get("peso"),
                        "febre": dados.get("febre"),
                        "febre_alta": dados.get("febre_alta"),
                        "dor_presente": dados.get("dor_presente"),
                        "dor_intensa": dados.get("dor_intensa"),
                        "toxemia": dados.get("toxemia"),
                        "prostracao": dados.get("prostracao"),
                        "secrecao_auricular": dados.get("secrecao_auricular"),
                        "secrecao_purulenta": dados.get("secrecao_purulenta"),
                        "duracao_dias": dados.get("duracao_dias")
                    }
                }

            if dados.get("alergia") is True:
                plano = self._resolve_otitis_therapeutic_plan(dados)
                resposta = self._build_structured_text(
                    avaliacao_clinica=avaliacao,
                    diagnostico_provavel="Quadro compatível com otite média aguda com relato de alergia à penicilina.",
                    conduta_recomendada=(
                        "Considerar alternativa terapêutica conforme protocolo institucional e perfil da reação alérgica."
                    ),
                    medicacao=plano["medicacao"],
                    dose=plano["dose"],
                    posologia=plano["posologia"],
                    duracao=plano["duracao"],
                    justificativa=(
                        "A alergia à penicilina interfere diretamente na escolha do antimicrobiano."
                    ),
                    observacoes_clinicas=(
                        "Individualizar a conduta conforme gravidade do quadro e tipo de alergia."
                    )
                )

                return {
                    "resposta": resposta,
                    "conduta": {
                        "cenario": scenario,
                        "gravidade": dados.get("gravidade"),
                        "alergia": True,
                        "idade": dados.get("idade"),
                        "peso": dados.get("peso"),
                        "febre": dados.get("febre"),
                        "febre_alta": dados.get("febre_alta"),
                        "dor_presente": dados.get("dor_presente"),
                        "dor_intensa": dados.get("dor_intensa"),
                        "toxemia": dados.get("toxemia"),
                        "prostracao": dados.get("prostracao"),
                        "secrecao_auricular": dados.get("secrecao_auricular"),
                        "secrecao_purulenta": dados.get("secrecao_purulenta"),
                        "duracao_dias": dados.get("duracao_dias")
                    }
                }

        return {
            "resposta": (
                "Consegui estruturar o caso clínico, mas não há protocolo específico implementado para esse cenário nesta etapa. "
                "Avalie o quadro clinicamente e siga o protocolo institucional disponível."
            ),
            "conduta": {
                "cenario": scenario,
                "dados_clinicos": dados
            }
        }
