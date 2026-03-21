from app.services.protocol_engine import ProtocolEngine


class ClinicalEngine:
    def __init__(self):
        self.protocol_engine = ProtocolEngine()

    def evaluate(self, question: str, contexto: dict = None):
        if contexto is None:
            contexto = {}

        scenario = contexto.get("scenario")
        dados = contexto.get("dados_clinicos", {})

        texto = question.lower()

        # Detectar piora clínica
        if "piora" in texto or "não melhorou" in texto or "sem melhora" in texto:
            return {
                "tipo": "reavaliacao",
                "cenario": scenario,
                "resposta": (
                    "O quadro sugere possível falha terapêutica ou evolução desfavorável.\n\n"
                    "Recomenda-se:\n"
                    "• Reavaliar diagnóstico\n"
                    "• Verificar adesão ao tratamento\n"
                    "• Considerar complicações\n"
                    "• Avaliar necessidade de troca de antibiótico\n"
                    "• Considerar encaminhamento se sinais de gravidade"
                ),
                "dados_clinicos": dados,
            }

        if not scenario:
            scenario = self.protocol_engine.identify_scenario(question)

        if not scenario:
            return {
                "tipo": "investigacao",
                "cenario": None,
                "resposta": "Preciso entender melhor o quadro clínico para orientar a conduta.",
                "perguntas": [
                    "Qual é a principal queixa do paciente?",
                    "Há quanto tempo os sintomas começaram?",
                    "Existe febre ou sinais sistêmicos?",
                    "Qual a idade do paciente?",
                ],
                "dados_clinicos": dados,
            }

        dados_extraidos = self._extract_clinical_data(question)
        dados.update({k: v for k, v in dados_extraidos.items() if v is not None})

        protocolo_base = self.protocol_engine.get_protocol(scenario)
        perguntas_protocolo = protocolo_base.get("perguntas_obrigatorias", []) if protocolo_base else []

        missing = []

        if perguntas_protocolo:
            for pergunta in perguntas_protocolo:
                p = pergunta.lower()

                if "idade" in p and dados.get("idade") is None:
                    missing.append(pergunta)
                elif "gravidade" in p and dados.get("gravidade") is None:
                    missing.append(pergunta)
                elif "alerg" in p and dados.get("alergia") is None:
                    missing.append(pergunta)
        else:
            if dados.get("idade") is None:
                missing.append("Qual a idade do paciente?")

            if dados.get("gravidade") is None:
                missing.append("Há sinais de gravidade, como febre alta, dor intensa ou toxemia?")

            if dados.get("alergia") is None:
                missing.append("O paciente tem alergia à penicilina?")

        if missing:
            return {
                "tipo": "coleta_dados",
                "cenario": scenario,
                "resposta": "Ainda preciso de algumas informações para definir o tratamento:",
                "perguntas": missing,
                "dados_clinicos": dados,
            }

        protocolo = self.protocol_engine.get_protocol(scenario)

        if not protocolo:
            return {
                "tipo": "erro",
                "cenario": scenario,
                "resposta": "Não encontrei protocolo para esse cenário.",
                "dados_clinicos": dados,
            }

        resposta_formatada = self._format_protocol(scenario, protocolo, dados)

        return {
            "tipo": "protocolo_definido",
            "cenario": scenario,
            "resposta": resposta_formatada,
            "dados_clinicos": dados,
        }

    def _extract_clinical_data(self, text: str):
        text = text.lower()

        data = {
            "idade": None,
            "peso": None,
            "alergia": None,
            "gravidade": None,
        }

        import re

        # IDADE
        match_idade = re.search(r"(\d+)\s*ano", text)
        if match_idade:
            data["idade"] = int(match_idade.group(1))

        # PESO
        match_peso = re.search(r"(\d+)\s*kg", text)
        if match_peso:
            data["peso"] = int(match_peso.group(1))

        # ALERGIA
        sinais_sem_alergia = [
            "sem alerg",
            "nega alerg",
            "nao tem alerg",
            "não tem alerg",
            "sem alergia",
            "nega alergia",
        ]

        if any(sinal in text for sinal in sinais_sem_alergia):
            data["alergia"] = False
        elif "alerg" in text:
            data["alergia"] = True

        # GRAVIDADE
        sinais_leves = [
            "sem febre",
            "afebril",
            "sem dor intensa",
            "dor leve",
            "sem sinais de gravidade",
            "sem gravidade",
            "sem toxemia",
            "bom estado geral",
        ]

        sinais_graves = [
            "febre alta",
            "toxemia",
            "prostrado",
            "dor intensa",
            "grave",
            "mal estado geral",
        ]

        if any(sinal in text for sinal in sinais_leves):
            data["gravidade"] = False
        elif any(sinal in text for sinal in sinais_graves):
            data["gravidade"] = True

        return data

    def _format_protocol(self, scenario, protocolo, dados):
        linhas = []

        linhas.append("Avaliação Clínica:")
        linhas.append(f"Diagnóstico provável: {scenario.replace('_', ' ').title()}")
        linhas.append("")

        tratamento = protocolo.get("tratamento", {})
        primeira = tratamento.get("primeira_linha")
        alergia_alt = tratamento.get("alergia_penicilina")
        alternativa = protocolo.get("alternativa")

        if dados.get("alergia") is True:
            if alergia_alt:
                med = alergia_alt
                motivo = "Devido à alergia à penicilina."
            elif alternativa:
                med = alternativa
                motivo = "Devido à alergia à penicilina."
            else:
                med = primeira
                motivo = "Sem alternativa específica disponível."
        else:
            med = primeira
            motivo = "Esquema de primeira linha."

        if not med:
            return "Protocolo encontrado, mas sem medicação configurada."

        linhas.append("Conduta recomendada:")
        linhas.append(f"Medicação: {med.get('medicamento', 'Não informado')}")
        linhas.append(f"Dose: {med.get('dose', med.get('posologia', 'Não informada'))}")
        linhas.append(f"Duração: {med.get('duracao', 'Não informada')}")
        linhas.append("")
        linhas.append(f"Justificativa: {motivo}")

        justificativa_protocolo = med.get("justificativa")
        if justificativa_protocolo:
            linhas.append(f"Observações clínicas: {justificativa_protocolo}")

        obs = protocolo.get("observacoes", [])
        if obs:
            linhas.append("")
            linhas.append("Observações clínicas:")
            for o in obs:
                linhas.append(f"• {o}")

        return "\n".join(linhas)
