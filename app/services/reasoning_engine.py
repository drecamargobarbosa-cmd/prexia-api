class ReasoningEngine:
    """
    Responsável por raciocínio clínico de prontidão.

    Não escolhe antibiótico.
    Não monta prescrição.
    Não aplica protocolo diretamente.

    Apenas decide:
    - há cenário suficiente?
    - já há dados mínimos para avançar?
    - quais dados faltam?
    """

    def evaluate_readiness(self, contexto: dict) -> dict:
        dados = contexto.get("dados_clinicos", {})
        scenario = contexto.get("scenario")

        if not scenario:
            return {
                "status": "insufficient_data",
                "reason": "Sem cenário clínico definido",
                "missing": [
                    "Qual é a hipótese clínica principal ou o diagnóstico suspeito?"
                ]
            }

        if scenario == "otite_media_aguda":
            return self._evaluate_otitis(dados)

        if scenario == "faringoamigdalite":
            return self._evaluate_pharyngotonsillitis(dados)

        if scenario == "sinusite":
            return self._evaluate_sinusitis(dados)

        return {
            "status": "insufficient_data",
            "reason": "Cenário ainda não suportado",
            "missing": [
                "Descreva melhor o quadro clínico para eu definir o cenário."
            ]
        }

    def _evaluate_otitis(self, dados: dict) -> dict:
        missing = []

        if dados.get("idade") is None:
            missing.append("Qual é a idade do paciente?")

        if dados.get("alergia") is None:
            missing.append("Há alergia à penicilina?")

        if dados.get("dor_presente") is None:
            missing.append("Há dor de ouvido ou otalgia?")

        if dados.get("duracao_dias") is None:
            missing.append("Há quantos dias os sintomas começaram?")

        if dados.get("febre") is None:
            missing.append("Há febre?")

        if dados.get("secrecao_auricular") is None:
            missing.append("Há secreção no ouvido ou otorreia?")

        if dados.get("dor_intensa") is None:
            missing.append("A dor é intensa?")

        if dados.get("toxemia") is None:
            missing.append("Há sinais de toxemia?")

        if dados.get("prostracao") is None:
            missing.append("O paciente apresenta prostração?")

        idade = dados.get("idade")
        if idade is not None and idade < 12 and dados.get("peso") is None:
            missing.append("Qual é o peso do paciente em kg?")

        if missing:
            return {
                "status": "need_more_data",
                "missing": missing
            }

        if dados.get("dor_presente") is True and (
            dados.get("febre") is True or
            dados.get("secrecao_auricular") is True or
            dados.get("dor_intensa") is True
        ):
            return {
                "status": "ready_for_treatment"
            }

        return {
            "status": "need_more_data",
            "missing": [
                "Preciso confirmar melhor os sinais clínicos para definir a conduta."
            ]
        }

    def _evaluate_pharyngotonsillitis(self, dados: dict) -> dict:
        missing = []

        if dados.get("idade") is None:
            missing.append("Qual é a idade do paciente?")

        if dados.get("alergia") is None:
            missing.append("Há alergia à penicilina?")

        if dados.get("febre") is None:
            missing.append("Há febre?")

        if dados.get("dor_garganta") is None:
            missing.append("Há dor de garganta ou odinofagia?")

        if dados.get("placas_amigdalianas") is None:
            missing.append("Há placas ou exsudato nas amígdalas?")

        if dados.get("duracao_dias") is None:
            missing.append("Há quantos dias os sintomas começaram?")

        idade = dados.get("idade")
        if idade is not None and idade < 12 and dados.get("peso") is None:
            missing.append("Qual é o peso do paciente em kg?")

        if missing:
            return {
                "status": "need_more_data",
                "missing": missing
            }

        if dados.get("dor_garganta") is True and (
            dados.get("febre") is True or
            dados.get("placas_amigdalianas") is True
        ):
            return {
                "status": "ready_for_treatment"
            }

        return {
            "status": "need_more_data",
            "missing": [
                "Preciso de mais elementos clínicos para sustentar conduta nesse quadro de garganta."
            ]
        }

    def _evaluate_sinusitis(self, dados: dict) -> dict:
        missing = []

        if dados.get("idade") is None:
            missing.append("Qual é a idade do paciente?")

        if dados.get("alergia") is None:
            missing.append("Há alergia à penicilina?")

        if dados.get("dor_facial") is None:
            missing.append("Há dor facial ou dor em seios da face?")

        if dados.get("secrecao_nasal_purulenta") is None:
            missing.append("Há secreção nasal purulenta?")

        if dados.get("duracao_dias") is None:
            missing.append("Há quantos dias os sintomas começaram?")

        idade = dados.get("idade")
        if idade is not None and idade < 12 and dados.get("peso") is None:
            missing.append("Qual é o peso do paciente em kg?")

        if missing:
            return {
                "status": "need_more_data",
                "missing": missing
            }

        if dados.get("dor_facial") is True and (
            dados.get("secrecao_nasal_purulenta") is True or
            (dados.get("duracao_dias") is not None and dados.get("duracao_dias") >= 10)
        ):
            return {
                "status": "ready_for_treatment"
            }

        return {
            "status": "need_more_data",
            "missing": [
                "Preciso confirmar melhor critérios clínicos para sinusite com indicação terapêutica."
            ]
        }
