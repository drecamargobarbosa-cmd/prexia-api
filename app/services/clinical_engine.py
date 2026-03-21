import re
from copy import deepcopy
from app.services.protocol_engine import ProtocolEngine


class ClinicalEngine:
    """
    Motor clínico com memória simples em RAM por user_id.

    Objetivos:
    - acumular dados clínicos entre mensagens
    - interpretar respostas curtas e fragmentadas
    - reconhecer afirmações e negações clínicas
    - evitar loop de perguntas repetidas
    - reconhecer intenção clínica, como pedido de antibiótico ou dose
    """

    MEMORY = {}

    def __init__(self):
        self.protocol_engine = ProtocolEngine()

    def evaluate(self, question: str, contexto: dict = None, user_id: str = "default"):
        if contexto is None:
            contexto = {}

        saved_context = self._get_saved_context(user_id)
        merged_context = self._merge_contexts(saved_context, contexto)
        merged_context = self._ensure_context_structure(merged_context)

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

        self._save_context(user_id, merged_context)

        return response

    def _get_saved_context(self, user_id: str) -> dict:
        return deepcopy(self.MEMORY.get(user_id, {}))

    def _save_context(self, user_id: str, context: dict):
        self.MEMORY[user_id] = deepcopy(context)

    def _merge_contexts(self, saved: dict, incoming: dict) -> dict:
        if not saved:
            return deepcopy(incoming or {})

        merged = deepcopy(saved)

        for key, value in (incoming or {}).items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._deep_merge_dicts(merged[key], value)
            elif value is not None:
                merged[key] = value

        return merged

    def _deep_merge_dicts(self, base: dict, new: dict) -> dict:
        result = deepcopy(base)

        for key, value in new.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = self._deep_merge_dicts(result[key], value)
            elif value is not None:
                result[key] = value

        return result

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
            "dor_intensa": None,
            "toxemia": None,
            "prostracao": None
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

        if any(term in t for term in [
            "qual antibiotico",
            "qual antibiotico indicado",
            "antibiotico indicado",
            "qual seria o antibiotico",
            "qual o antibiotico"
        ]):
            return "antibiotico"

        if any(term in t for term in [
            "qual dose",
            "dosagem",
            "quanto mg",
            "posologia"
        ]):
            return "dose"

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

        dor_intensa = self._extract_pain_status(t)
        if dor_intensa is not None:
            dados["dor_intensa"] = dor_intensa

        toxemia = self._extract_toxemia_status(t)
        if toxemia is not None:
            dados["toxemia"] = toxemia

        prostracao = self._extract_prostration_status(t)
        if prostracao is not None:
            dados["prostracao"] = prostracao

        idade = self._extract_age(t)
        if idade is not None:
            dados["idade"] = idade

        peso = self._extract_weight(t)
        if peso is not None:
            dados["peso"] = peso

        explicit_gravity = self._extract_explicit_gravity_status(t)
        if explicit_gravity is not None:
            dados["gravidade"] = explicit_gravity
        else:
            inferred = self._infer_gravity_from_signs(dados)
            if inferred is not None:
                dados["gravidade"] = inferred

        context["dados_clinicos"] = dados
        return context

    def _contains_any(self, text: str, terms: list[str]) -> bool:
        return any(term in text for term in terms)

    def _extract_allergy_status(self, text: str):
        negative_terms = [
            "sem alergia",
            "sem alergias",
            "nao tem alergia",
            "nao possui alergia",
            "nega alergia",
            "nega alergias"
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

        if self._contains_any(text, negative_terms):
            return False

        if self._contains_any(text, positive_terms):
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
            "febre",
            "febril",
            "febre alta",
            "temperatura elevada"
        ]

        if self._contains_any(text, negative_terms):
            return False

        if self._contains_any(text, positive_terms):
            return True

        return None

    def _extract_pain_status(self, text: str):
        negative_terms = [
            "sem dor",
            "nega dor",
            "nao tem dor",
            "nao apresenta dor",
            "sem dor intensa",
            "dor leve",
            "dor moderada"
        ]

        positive_terms = [
            "tem dor",
            "com dor",
            "apresenta dor",
            "dor intensa",
            "muita dor",
            "dor forte",
            "otalgia intensa",
            "dor importante"
        ]

        if self._contains_any(text, negative_terms):
            return False

        if self._contains_any(text, positive_terms):
            return True

        return None

    def _extract_toxemia_status(self, text: str):
        negative_terms = [
            "sem toxemia",
            "nega toxemia",
            "nao apresenta toxemia"
        ]

        positive_terms = [
            "tem toxemia",
            "com toxemia",
            "apresenta toxemia",
            "toxemia",
            "toxico",
            "toxemico"
        ]

        if self._contains_any(text, negative_terms):
            return False

        if self._contains_any(text, positive_terms):
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
            "estado geral ruim"
        ]

        if self._contains_any(text, negative_terms):
            return False

        if self._contains_any(text, positive_terms):
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
            "quadro grave",
            "grave"
        ]

        if self._contains_any(text, negative_terms):
            return False

        if self._contains_any(text, positive_terms):
            return True

        return None

    def _infer_gravity_from_signs(self, dados: dict):
        signs = [
            dados.get("febre"),
            dados.get("dor_intensa"),
            dados.get("toxemia"),
            dados.get("prostracao")
        ]

        if any(value is True for value in signs):
            return True

        known_signs = [value for value in signs if value is not None]
        if len(known_signs) > 0 and all(value is False for value in known_signs):
            return False

        return None

    def _extract_age(self, text: str):
        patterns = [
            r'(\d{1,3})\s*anos',
            r'idade\s*[:=]?\s*(\d{1,3})',
            r'paciente\s*de\s*(\d{1,3})\s*anos'
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
                "context": {
                    "scenario": scenario,
                    "dados_clinicos": dados
                }
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
                "context": {
                    "scenario": scenario,
                    "dados_clinicos": dados
                }
            }

        if intent == "antibiotico":
            return self._generate_antibiotic_response(context)

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
            "context": {
                "scenario": scenario,
                "dados_clinicos": dados
            }
        }

    def _get_missing_questions(self, scenario: str, dados: dict):
        questions = []

        if dados.get("gravidade") is None:
            questions.append(
                "Há sinais de gravidade, como febre alta, dor intensa, toxemia ou prostração?"
            )

        if dados.get("alergia") is None:
            questions.append("O paciente tem alergia à penicilina?")

        if dados.get("idade") is None:
            questions.append("Qual é a idade do paciente?")

        idade = dados.get("idade")
        if idade is not None and idade < 12 and dados.get("peso") is None:
            questions.append("Qual é o peso do paciente em kg?")

        return questions

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

    def _generate_antibiotic_response(self, context: dict):
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})

        if scenario == "otite_media_aguda":
            if dados.get("alergia") is False:
                return {
                    "resposta": (
                        "Para otite média aguda sem sinais de gravidade e sem alergia à penicilina, "
                        "o antibiótico de primeira escolha costuma ser a amoxicilina, conforme protocolo institucional. "
                        "Em adultos, uma posologia frequentemente utilizada é 500 mg a cada 8 horas ou 875 mg a cada 12 horas, "
                        "mas a escolha final deve seguir o protocolo adotado no serviço, a avaliação clínica e o perfil do paciente."
                    ),
                    "clinical_response": {
                        "tipo": "antibiotico",
                        "cenario": scenario,
                        "resposta": (
                            "Para otite média aguda sem sinais de gravidade e sem alergia à penicilina, "
                            "o antibiótico de primeira escolha costuma ser a amoxicilina, conforme protocolo institucional."
                        ),
                        "antibiotico": "amoxicilina",
                        "dados_clinicos": dados
                    },
                    "history": context.get("history", []),
                    "context": {
                        "scenario": scenario,
                        "dados_clinicos": dados
                    }
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
                    "context": {
                        "scenario": scenario,
                        "dados_clinicos": dados
                    }
                }

        return {
            "resposta": "Ainda não há protocolo específico de antibiótico implementado para esse cenário.",
            "clinical_response": {
                "tipo": "antibiotico",
                "cenario": scenario,
                "dados_clinicos": dados
            },
            "history": context.get("history", []),
            "context": {
                "scenario": scenario,
                "dados_clinicos": dados
            }
        }

    def _generate_dose_response(self, context: dict):
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})

        if scenario == "otite_media_aguda" and dados.get("alergia") is False:
            idade = dados.get("idade")
            peso = dados.get("peso")

            if idade is not None and idade >= 12:
                resposta = (
                    "Para adulto com otite média aguda e sem alergia à penicilina, "
                    "uma posologia comumente utilizada para amoxicilina é 500 mg a cada 8 horas "
                    "ou 875 mg a cada 12 horas, conforme avaliação clínica e protocolo institucional."
                )
            elif peso is not None:
                resposta = (
                    f"Para paciente pediátrico com {peso} kg, a dose deve ser calculada por peso, "
                    "conforme protocolo institucional adotado pelo serviço."
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
                    "dados_clinicos": dados
                },
                "history": context.get("history", []),
                "context": {
                    "scenario": scenario,
                    "dados_clinicos": dados
                }
            }

        return {
            "resposta": "Ainda não há protocolo de dose específico implementado para esse cenário.",
            "clinical_response": {
                "tipo": "dose",
                "cenario": scenario,
                "dados_clinicos": dados
            },
            "history": context.get("history", []),
            "context": {
                "scenario": scenario,
                "dados_clinicos": dados
            }
        }

    def _fallback_response(self, scenario: str, dados: dict):
        if scenario == "otite_media_aguda":
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
                        "dor_intensa": dados.get("dor_intensa"),
                        "toxemia": dados.get("toxemia"),
                        "prostracao": dados.get("prostracao")
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
                        "dor_intensa": dados.get("dor_intensa"),
                        "toxemia": dados.get("toxemia"),
                        "prostracao": dados.get("prostracao")
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
                        "dor_intensa": dados.get("dor_intensa"),
                        "toxemia": dados.get("toxemia"),
                        "prostracao": dados.get("prostracao")
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
