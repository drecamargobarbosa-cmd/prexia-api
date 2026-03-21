import re
from copy import deepcopy
from app.services.protocol_engine import ProtocolEngine


class ClinicalEngine:
    """
    Motor clínico com memória simples em memória RAM, por user_id.
    Objetivo:
    - acumular dados clínicos a cada mensagem
    - interpretar respostas fragmentadas
    - evitar loop de perguntas repetidas
    """

    # memória simples por usuário
    MEMORY = {}

    def __init__(self):
        self.protocol_engine = ProtocolEngine()

    def evaluate(self, question: str, contexto: dict = None, user_id: str = "default"):
        if contexto is None:
            contexto = {}

        # 1. Recupera contexto salvo
        saved_context = self._get_saved_context(user_id)

        # 2. Faz merge do contexto recebido com o salvo
        merged_context = self._merge_contexts(saved_context, contexto)

        # 3. Garante estrutura mínima
        merged_context = self._ensure_context_structure(merged_context)

        # 4. Detecta cenário, se ainda não houver
        scenario = merged_context.get("scenario")
        if not scenario:
            scenario = self._detect_scenario(question)
            if scenario:
                merged_context["scenario"] = scenario

        # 5. Extrai dados da mensagem atual e acumula
        merged_context = self._extract_and_update_clinical_data(question, merged_context)

        # 6. Atualiza histórico
        merged_context["history"].append({
            "role": "user",
            "content": question
        })

        # 7. Decide resposta
        response = self._build_response(merged_context)

        # 8. Salva resposta no histórico
        merged_context["history"].append({
            "role": "assistant",
            "content": response["resposta"]
        })

        # 9. Persiste contexto atualizado
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
            "gravidade": None
        }

        for key, value in defaults.items():
            if key not in context["dados_clinicos"]:
                context["dados_clinicos"][key] = value

        return context

    def _detect_scenario(self, text: str):
        t = self._normalize(text)

        if any(term in t for term in ["dor de ouvido", "otite", "ouvido inflamado"]):
            return "otite_media_aguda"

        if any(term in t for term in ["sinusite", "dor na face", "seios da face"]):
            return "sinusite"

        if any(term in t for term in ["dor de garganta", "amigdalite", "faringite"]):
            return "faringoamigdalite"

        return None

    def _extract_and_update_clinical_data(self, text: str, context: dict) -> dict:
        dados = context["dados_clinicos"]
        t = self._normalize(text)

        # alergia
        if "sem alergia" in t or "nao tem alergia" in t or "não tem alergia" in t:
            dados["alergia"] = False
        elif "alergia a penicilina" in t or "alergico a penicilina" in t or "alérgico a penicilina" in t:
            dados["alergia"] = True
        elif "com alergia" in t or "tem alergia" in t or "alergico" in t or "alérgico" in t:
            dados["alergia"] = True

        # gravidade
        if "sem gravidade" in t or "sem sinais de gravidade" in t:
            dados["gravidade"] = False
        elif any(term in t for term in [
            "grave", "gravidade", "toxemia", "febre alta", "dor intensa", "prostrado"
        ]):
            if "sem gravidade" not in t and "sem sinais de gravidade" not in t:
                dados["gravidade"] = True

        # idade
        idade = self._extract_age(t)
        if idade is not None:
            dados["idade"] = idade

        # peso
        peso = self._extract_weight(t)
        if peso is not None:
            dados["peso"] = peso

        context["dados_clinicos"] = dados
        return context

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
            r'peso\s*[:=]?\s*(\d{1,3})'
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

        if not scenario:
            return {
                "resposta": "Preciso entender melhor o quadro clínico para orientar a conduta.",
                "clinical_response": {
                    "tipo": "coleta_dados",
                    "cenario": None,
                    "resposta": "Preciso entender melhor o quadro clínico para orientar a conduta.",
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
            questions.append("Há sinais de gravidade, como febre alta, dor intensa ou toxemia?")

        if dados.get("alergia") is None:
            questions.append("O paciente tem alergia à penicilina?")

        # Idade é importante para definir conduta pediátrica vs adulto
        if dados.get("idade") is None:
            questions.append("Qual é a idade do paciente?")

        # Peso só perguntar se for criança
        idade = dados.get("idade")
        if idade is not None and idade < 12 and dados.get("peso") is None:
            questions.append("Qual é o peso do paciente em kg?")

        return questions

    def _generate_protocol_response(self, scenario: str, dados: dict):
        """
        Aqui você pode integrar com seu ProtocolEngine real.
        Mantive um fallback para evitar quebra durante o teste.
        """
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

    def _fallback_response(self, scenario: str, dados: dict):
        if scenario == "otite_media_aguda":
            if dados.get("gravidade") is False and dados.get("alergia") is False:
                return {
                    "resposta": (
                        "Com base nas informações fornecidas, trata-se de um quadro compatível com otite média aguda sem sinais de gravidade e sem alergia à penicilina. "
                        "Considere avaliar indicação de antibioticoterapia conforme protocolo institucional, além de analgesia e reavaliação clínica se não houver melhora."
                    ),
                    "conduta": {
                        "cenario": scenario,
                        "gravidade": dados.get("gravidade"),
                        "alergia": dados.get("alergia"),
                        "idade": dados.get("idade")
                    }
                }

            if dados.get("gravidade") is False and dados.get("alergia") is True:
                return {
                    "resposta": (
                        "Com base nas informações fornecidas, trata-se de um quadro compatível com otite média aguda sem sinais de gravidade, porém com relato de alergia à penicilina. "
                        "Considere alternativa terapêutica conforme protocolo institucional e gravidade da alergia relatada."
                    ),
                    "conduta": {
                        "cenario": scenario,
                        "gravidade": dados.get("gravidade"),
                        "alergia": dados.get("alergia"),
                        "idade": dados.get("idade")
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

    def _normalize(self, text: str) -> str:
        if not text:
            return ""
        return text.strip().lower()
