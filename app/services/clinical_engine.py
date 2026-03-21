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

        if missing:
            return {
                "tipo": "coleta_dados",
                "cenario": scenario,
                "resposta": "Ainda preciso de algumas informações para definir o tratamento:",
                "perguntas": missing,
                "dados_clinicos": dados,
            }

        protocolo = self.protocol_engine.get_protocol(scenario)

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

        match_idade = re.search(r"(\d+)\s*ano", text)
        if match_idade:
            data["idade"] = int(match_idade.group(1))

        if any(s in text for s in ["sem alerg", "sem alergia", "nega alerg"]):
            data["alergia"] = False
        elif "alerg" in text:
            data["alergia"] = True

        sinais_leves = ["sem febre", "afebril", "sem gravidade", "dor leve"]
        sinais_graves = ["febre alta", "toxemia", "prostrado", "grave"]

        if any(s in text for s in sinais_leves):
            data["gravidade"] = False
        elif any(s in text for s in sinais_graves):
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

        med = alergia_alt if dados.get("alergia") else primeira

        if not med:
            return "Protocolo sem medicação configurada."

        # 🔥 FORMATO DE PRESCRIÇÃO REAL
        linhas.append("Conduta recomendada:")

        linhas.append(f"{med.get('medicamento')} {med.get('apresentacao')}")
        linhas.append("")
        linhas.append(f"{med.get('posologia')} por {med.get('duracao')}")
        linhas.append("")
        linhas.append(f"Quantidade: {med.get('quantidade_total')}")
        linhas.append("")
        linhas.append(f"Justificativa: {med.get('justificativa')}")

        return "\n".join(linhas)
