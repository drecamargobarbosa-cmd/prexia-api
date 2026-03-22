class ReasoningEngine:
    """
    Responsável por raciocínio clínico de prontidão.

    Não escolhe antibiótico.
    Não monta prescrição.
    Não aplica protocolo diretamente.

    Decide:
    - se o cenário já tem dados suficientes para avançar
    - quais informações ainda faltam
    - quais perguntas são prioritárias
    - se existem sinais de maior gravidade
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
                ],
                "priority": "high"
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
            ],
            "priority": "medium"
        }

    def _evaluate_otitis(self, dados: dict) -> dict:
        idade = dados.get("idade")
        peso = dados.get("peso")
        alergia = dados.get("alergia")
        dor_presente = dados.get("dor_presente")
        dor_intensa = dados.get("dor_intensa")
        febre = dados.get("febre")
        secrecao_auricular = dados.get("secrecao_auricular")
        toxemia = dados.get("toxemia")
        prostracao = dados.get("prostracao")
        duracao_dias = dados.get("duracao_dias")

        # 1. dados-base realmente necessários
        core_missing = []
        if idade is None:
            core_missing.append("Qual é a idade do paciente?")
        if alergia is None:
            core_missing.append("Há alergia à penicilina?")
        if dor_presente is None:
            core_missing.append("Há dor de ouvido ou otalgia?")
        if duracao_dias is None:
            core_missing.append("Há quantos dias os sintomas começaram?")

        # 2. sinais clínicos que sustentam decisão
        supportive_known = [v for v in [febre, secrecao_auricular, dor_intensa] if v is not None]
        supportive_positive = any(v is True for v in [febre, secrecao_auricular, dor_intensa])

        # 3. sinais de maior gravidade
        severe_positive = any(v is True for v in [toxemia, prostracao, dor_intensa])

        # 4. peso só é obrigatório em pediatria
        peso_missing = []
        if idade is not None and idade < 12 and peso is None:
            peso_missing.append("Qual é o peso do paciente em kg?")

        # 5. se faltam dados-base, ainda não dá para avançar
        if core_missing:
            return {
                "status": "need_more_data",
                "missing": core_missing,
                "priority": "high"
            }

        # 6. se já temos base clínica forte, pode avançar mesmo sem tudo
        if dor_presente is True and supportive_positive:
            if idade is not None and idade < 12 and peso is None:
                return {
                    "status": "need_more_data",
                    "missing": peso_missing,
                    "priority": "high"
                }

            return {
                "status": "ready_for_treatment",
                "priority": "high" if severe_positive else "medium",
                "confidence": "moderate" if severe_positive else "good"
            }

        # 7. se ainda não há suporte clínico suficiente, perguntar o que mais importa
        missing = []
        if febre is None:
            missing.append("Há febre?")
        if secrecao_auricular is None:
            missing.append("Há secreção no ouvido ou otorreia?")
        if dor_intensa is None:
            missing.append("A dor é intensa?")

        # sinais de gravidade vêm depois da base, mas ainda importam
        if toxemia is None:
            missing.append("Há sinais de toxemia?")
        if prostracao is None:
            missing.append("O paciente apresenta prostração?")

        if idade is not None and idade < 12 and peso is None:
            missing.append("Qual é o peso do paciente em kg?")

        return {
            "status": "need_more_data",
            "missing": missing,
            "priority": "medium"
        }

    def _evaluate_pharyngotonsillitis(self, dados: dict) -> dict:
        idade = dados.get("idade")
        peso = dados.get("peso")
        alergia = dados.get("alergia")
        febre = dados.get("febre")
        dor_garganta = dados.get("dor_garganta")
        placas = dados.get("placas_amigdalianas")
        duracao_dias = dados.get("duracao_dias")
        toxemia = dados.get("toxemia")
        prostracao = dados.get("prostracao")

        core_missing = []
        if idade is None:
            core_missing.append("Qual é a idade do paciente?")
        if alergia is None:
            core_missing.append("Há alergia à penicilina?")
        if dor_garganta is None:
            core_missing.append("Há dor de garganta ou odinofagia?")
        if duracao_dias is None:
            core_missing.append("Há quantos dias os sintomas começaram?")

        if core_missing:
            return {
                "status": "need_more_data",
                "missing": core_missing,
                "priority": "high"
            }

        severe_positive = any(v is True for v in [toxemia, prostracao])

        if dor_garganta is True and (febre is True or placas is True):
            if idade is not None and idade < 12 and peso is None:
                return {
                    "status": "need_more_data",
                    "missing": ["Qual é o peso do paciente em kg?"],
                    "priority": "high"
                }

            return {
                "status": "ready_for_treatment",
                "priority": "high" if severe_positive else "medium",
                "confidence": "moderate" if severe_positive else "good"
            }

        missing = []
        if febre is None:
            missing.append("Há febre?")
        if placas is None:
            missing.append("Há placas ou exsudato nas amígdalas?")
        if toxemia is None:
            missing.append("Há sinais de toxemia?")
        if prostracao is None:
            missing.append("O paciente apresenta prostração?")

        if idade is not None and idade < 12 and peso is None:
            missing.append("Qual é o peso do paciente em kg?")

        return {
            "status": "need_more_data",
            "missing": missing,
            "priority": "medium"
        }

    def _evaluate_sinusitis(self, dados: dict) -> dict:
        idade = dados.get("idade")
        peso = dados.get("peso")
        alergia = dados.get("alergia")
        dor_facial = dados.get("dor_facial")
        secrecao_nasal_purulenta = dados.get("secrecao_nasal_purulenta")
        duracao_dias = dados.get("duracao_dias")
        febre = dados.get("febre")
        toxemia = dados.get("toxemia")
        prostracao = dados.get("prostracao")

        core_missing = []
        if idade is None:
            core_missing.append("Qual é a idade do paciente?")
        if alergia is None:
            core_missing.append("Há alergia à penicilina?")
        if dor_facial is None:
            core_missing.append("Há dor facial ou dor em seios da face?")
        if duracao_dias is None:
            core_missing.append("Há quantos dias os sintomas começaram?")

        if core_missing:
            return {
                "status": "need_more_data",
                "missing": core_missing,
                "priority": "high"
            }

        severe_positive = any(v is True for v in [toxemia, prostracao])

        criteria_positive = False
        if dor_facial is True and secrecao_nasal_purulenta is True:
            criteria_positive = True
        if dor_facial is True and duracao_dias is not None and duracao_dias >= 10:
            criteria_positive = True
        if febre is True and duracao_dias is not None and duracao_dias >= 3:
            criteria_positive = True

        if criteria_positive:
            if idade is not None and idade < 12 and peso is None:
                return {
                    "status": "need_more_data",
                    "missing": ["Qual é o peso do paciente em kg?"],
                    "priority": "high"
                }

            return {
                "status": "ready_for_treatment",
                "priority": "high" if severe_positive else "medium",
                "confidence": "moderate" if severe_positive else "good"
            }

        missing = []
        if secrecao_nasal_purulenta is None:
            missing.append("Há secreção nasal purulenta?")
        if febre is None:
            missing.append("Há febre?")
        if toxemia is None:
            missing.append("Há sinais de toxemia?")
        if prostracao is None:
            missing.append("O paciente apresenta prostração?")

        if idade is not None and idade < 12 and peso is None:
            missing.append("Qual é o peso do paciente em kg?")

        return {
            "status": "need_more_data",
            "missing": missing,
            "priority": "medium"
        }
