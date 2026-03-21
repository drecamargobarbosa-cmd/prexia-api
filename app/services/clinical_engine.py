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

    def _detect_scenario(self, text: str):
        t = self._normalize(text)

        if any(term in t for term in [
            "dor de ouvido",
            "otite",
            "ouvido inflamado",
            "ouvido doendo",
            "otalgia"
        ]):
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
            "ouvido doendo",
            "otalgia",
            "dor no ouvido",
            "paciente com dor",
            "dor,"
        ]

        if self._contains_any_expression(text, negative_terms):
            return False

        if self._contains_any_expression(text, positive_terms) or text.startswith("dor"):
            return True

        return None

    def _extract_pain_intensity_status(self, text: str):
        negative_terms = [
            "sem dor intensa",
            "dor leve",
            "dor moderada",
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
            "nega prostracao",
            "nao prostrado",
            "nao esta prostrado",
            "ativo",
            "bom estado geral"
        ]

        positive_terms = [
            "tem prostracao",
            "com prostracao",
            "apresenta prostracao",
            "prostrado",
            "prostracao",
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
        patterns = [
            r'ha\s*(\d{1,2})\s*dias',
            r'(\d{1,2})\s*dias\s*de\s*sintomas',
            r'(\d{1,2})\s*dias\s*de\s*dor',
            r'comecou\s*ha\s*(\d{1,2})\s*dias',
            r'inicio\s*ha\s*(\d{1,2})\s*dias',
            r'sintomas\s*ha\s*(\d{1,2})\s*dias',
            r'(\d{1,2})\s*dias\s*de\s*evolucao'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
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

        if scenario == "otite_media_aguda" and not self._has_minimum_diagnostic_support_for_otitis(dados):
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

            if dados.get("febre_alta") is None:
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
            if dados.get("febre_alta") is None:
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
            if not self._has_minimum_diagnostic_support_for_otitis(dados):
                resposta = (
                    "Antes de definir tratamento para otite, preciso de sinais e sintomas mais consistentes do quadro, "
                    "como febre, secreção auricular, intensidade da dor e tempo de evolução."
                )
                return {
                    "resposta": resposta,
                    "clinical_response": {
                        "tipo": "tratamento",
                        "cenario": scenario,
                        "resposta": resposta,
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

            if dados.get("alergia") is True:
                if dados.get("gravidade") is True:
                    resposta = (
                        "Para quadro compatível com otite média aguda, com alergia à penicilina e sinais de gravidade, "
                        "a conduta deve ser individualizada conforme avaliação clínica, perfil da alergia e protocolo institucional. "
                        "Considere alternativa ao esquema com penicilina, além de analgesia, reavaliação precoce e monitoramento clínico."
                    )
                else:
                    resposta = (
                        "Para quadro compatível com otite média aguda, com alergia à penicilina e dados clínicos mínimos já levantados, "
                        "considerar alternativa terapêutica conforme protocolo institucional, além de analgesia e reavaliação clínica."
                    )

                return {
                    "resposta": resposta,
                    "clinical_response": {
                        "tipo": "tratamento",
                        "cenario": scenario,
                        "resposta": resposta,
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

            if dados.get("alergia") is False:
                if dados.get("gravidade") is True:
                    resposta = (
                        "Para quadro compatível com otite média aguda com sinais de gravidade, a conduta deve considerar avaliação clínica mais cuidadosa, "
                        "definição do antibiótico conforme protocolo institucional, analgesia e reavaliação precoce."
                    )
                else:
                    resposta = (
                        "Para quadro compatível com otite média aguda, sem sinais de gravidade e sem alergia à penicilina, "
                        "considerar antibioticoterapia conforme protocolo institucional, além de analgesia e reavaliação clínica."
                    )

                return {
                    "resposta": resposta,
                    "clinical_response": {
                        "tipo": "tratamento",
                        "cenario": scenario,
                        "resposta": resposta,
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

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
            if not self._has_minimum_diagnostic_support_for_otitis(dados):
                return {
                    "resposta": (
                        "Ainda não há base clínica suficiente para indicar antibiótico com segurança. "
                        "Preciso confirmar melhor febre, secreção auricular, intensidade da dor e tempo de evolução."
                    ),
                    "clinical_response": {
                        "tipo": "antibiotico",
                        "cenario": scenario,
                        "resposta": (
                            "Ainda não há base clínica suficiente para indicar antibiótico com segurança."
                        ),
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

            if dados.get("alergia") is False and dados.get("gravidade") is False:
                return {
                    "resposta": (
                        "Para quadro compatível com otite média aguda, sem sinais de gravidade e sem alergia à penicilina, "
                        "o antibiótico de primeira escolha costuma ser a amoxicilina, conforme protocolo institucional."
                    ),
                    "clinical_response": {
                        "tipo": "antibiotico",
                        "cenario": scenario,
                        "resposta": (
                            "Para quadro compatível com otite média aguda, sem sinais de gravidade e sem alergia à penicilina, "
                            "o antibiótico de primeira escolha costuma ser a amoxicilina, conforme protocolo institucional."
                        ),
                        "antibiotico": "amoxicilina",
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

            if dados.get("alergia") is False and dados.get("gravidade") is True:
                return {
                    "resposta": (
                        "Há sinais de gravidade no quadro. A definição do antibiótico precisa considerar avaliação clínica mais cuidadosa "
                        "e o protocolo institucional adotado pelo serviço."
                    ),
                    "clinical_response": {
                        "tipo": "antibiotico",
                        "cenario": scenario,
                        "resposta": "Há sinais de gravidade no quadro.",
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

            if dados.get("alergia") is True:
                return {
                    "resposta": (
                        "Em caso de alergia à penicilina, considerar alternativas como azitromicina ou claritromicina, "
                        "conforme gravidade da alergia, características do paciente e protocolo institucional."
                    ),
                    "clinical_response": {
                        "tipo": "antibiotico",
                        "cenario": scenario,
                        "resposta": (
                            "Em caso de alergia à penicilina, considerar alternativas como azitromicina ou claritromicina."
                        ),
                        "alternativa": True,
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

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
            if not self._has_minimum_diagnostic_support_for_otitis(dados):
                return {
                    "resposta": (
                        "Ainda não há dados clínicos suficientes para definir o medicamento com segurança. "
                        "Preciso confirmar melhor o quadro antes de avançar."
                    ),
                    "clinical_response": {
                        "tipo": "medicamento",
                        "cenario": scenario,
                        "resposta": (
                            "Ainda não há dados clínicos suficientes para definir o medicamento com segurança."
                        ),
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

            if dados.get("alergia") is True:
                return {
                    "resposta": (
                        "Com relato de alergia à penicilina, o medicamento deve ser uma alternativa ao grupo das penicilinas, "
                        "como azitromicina ou claritromicina, conforme protocolo institucional e perfil da reação alérgica."
                    ),
                    "clinical_response": {
                        "tipo": "medicamento",
                        "cenario": scenario,
                        "resposta": (
                            "Com relato de alergia à penicilina, considerar alternativa como azitromicina ou claritromicina."
                        ),
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

            if dados.get("alergia") is False:
                return {
                    "resposta": (
                        "Sem alergia à penicilina, o medicamento de primeira escolha costuma ser a amoxicilina, "
                        "conforme protocolo institucional."
                    ),
                    "clinical_response": {
                        "tipo": "medicamento",
                        "cenario": scenario,
                        "resposta": "Sem alergia à penicilina, o medicamento de primeira escolha costuma ser a amoxicilina.",
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

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
            if not self._has_minimum_diagnostic_support_for_otitis(dados):
                return {
                    "resposta": (
                        "Antes de definir dose, preciso ter mais segurança sobre a indicação clínica do antibiótico."
                    ),
                    "clinical_response": {
                        "tipo": "dose",
                        "cenario": scenario,
                        "resposta": (
                            "Antes de definir dose, preciso ter mais segurança sobre a indicação clínica do antibiótico."
                        ),
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

            if dados.get("alergia") is True:
                return {
                    "resposta": (
                        "Como há relato de alergia à penicilina, a dose depende do antibiótico alternativo escolhido, "
                        "como azitromicina ou claritromicina. A definição da posologia deve seguir o protocolo institucional, "
                        "a idade, o peso quando aplicável, e o perfil clínico do paciente."
                    ),
                    "clinical_response": {
                        "tipo": "dose",
                        "cenario": scenario,
                        "resposta": (
                            "Com alergia à penicilina, a dose depende do antibiótico alternativo escolhido."
                        ),
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

            if dados.get("alergia") is False:
                idade = dados.get("idade")
                peso = dados.get("peso")

                if idade is not None and idade >= 12:
                    resposta = (
                        "Para adulto sem alergia à penicilina, a dose deve seguir o protocolo institucional do serviço para amoxicilina."
                    )
                elif peso is not None:
                    resposta = (
                        f"Para paciente pediátrico com {peso} kg, a dose deve ser calculada por peso, conforme protocolo institucional."
                    )
                else:
                    resposta = (
                        "Para definir a dose com maior segurança, preciso da idade e, se for criança, também do peso."
                    )

                return {
                    "resposta": resposta,
                    "clinical_response": {
                        "tipo": "dose",
                        "cenario": scenario,
                        "resposta": resposta,
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": context
                }

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
            if not self._has_minimum_diagnostic_support_for_otitis(dados):
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
                return {
                    "resposta": (
                        "Com base nas informações fornecidas, trata-se de um quadro compatível com otite média aguda "
                        "sem sinais de gravidade e sem alergia à penicilina. Considere avaliar indicação de antibioticoterapia "
                        "conforme protocolo institucional, além de analgesia e reavaliação clínica se não houver melhora."
                    ),
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
                return {
                    "resposta": (
                        "O quadro sugere otite média aguda com sinais de gravidade. "
                        "É necessário avaliar com maior cautela, considerando intensidade dos sintomas, estado geral, "
                        "necessidade de reavaliação precoce e conduta conforme protocolo institucional."
                    ),
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
                return {
                    "resposta": (
                        "Com base nas informações fornecidas, trata-se de um quadro compatível com otite média aguda "
                        "com relato de alergia à penicilina. Considere alternativa terapêutica conforme protocolo institucional "
                        "e perfil da reação alérgica."
                    ),
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
