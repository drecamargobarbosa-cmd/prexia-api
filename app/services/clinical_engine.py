from app.services.protocol_engine import ProtocolEngine


class ClinicalEngine:
    def __init__(self):
        self.protocol_engine = ProtocolEngine()

    def evaluate(self, question: str, contexto: dict = None):
        if contexto is None:
            contexto = {}

        scenario = contexto.get("scenario")
        dados = contexto.get("dados_clinicos", {})

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

        protocolo_base = self.protocol_engine.load_protocol(scenario)
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

        protocolo = self.protocol_engine.get_protocol(scenario, dados)

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

        if "ano" in text:
            import re
            match = re.search(r"(\d+)\s*ano", text)
            if match:
                data["idade"] = int(match.group(1))

        if "kg" in text:
            import re
            match = re.search(r"(\d+)\s*kg", text)
            if match:
                data["peso"] = int(match.group(1))

        if "sem alerg" in text:
            data["alergia"] = False
        elif "alerg" in text:
            data["alergia"] = True

        if "sem grav" in text:
            data["gravidade"] = False
        elif "grave" in text or "toxemia" in text:
            data["gravidade"] = True

        return data

    def _format_protocol(self, scenario, protocolo, dados):
        linhas = []

        linhas.append(f"Diagnóstico: {scenario.replace('_', ' ').title()}\n")

        primeira = protocolo.get("primeira_linha")
        alergia_alt = protocolo.get("alergia_penicilina")
        alternativa = protocolo.get("alternativa")

        usar_alternativa = False

        if dados.get("alergia") is True:
            if alergia_alt:
                usar_alternativa = True
                med = alergia_alt
            elif alternativa:
                usar_alternativa = True
                med = alternativa
            else:
                med = primeira
        else:
            med = primeira

        linhas.append("Conduta:")
        linhas.append(f"• {med['medicamento']}")
        linhas.append(f"• Dose: {med['dose']}")
        linhas.append(f"• Duração: {med['duracao']}\n")

        if usar_alternativa:
            linhas.append("Atenção:")
            linhas.append("• Escolha baseada em alergia à penicilina\n")

        obs = protocolo.get("observacoes", [])
        if obs:
            linhas.append("Observações:")
            for o in obs:
                linhas.append(f"• {o}")

        return "\n".join(linhas)
