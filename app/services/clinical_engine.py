import re
import unicodedata

from app.services.protocol_engine import ProtocolEngine


class ClinicalEngine:
    def __init__(self):
        self.protocol_engine = ProtocolEngine()

    def evaluate(self, question: str, contexto: dict = None):
        if contexto is None:
            contexto = {}

        scenario = contexto.get("scenario")
        dados = contexto.get("dados_clinicos", {})

        texto_normalizado = self._normalize_text(question)

        if self._is_worsening_message(texto_normalizado):
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

        dados_atualizados = {
            "idade": dados.get("idade"),
            "peso": dados.get("peso"),
            "alergia": dados.get("alergia"),
            "gravidade": dados.get("gravidade"),
        }

        for chave, valor in dados_extraidos.items():
            if valor is not None:
                dados_atualizados[chave] = valor

        protocolo_base = self.protocol_engine.get_protocol(scenario)
        perguntas_protocolo = protocolo_base.get("perguntas_obrigatorias", []) if protocolo_base else []

        missing = self._get_missing_questions(perguntas_protocolo, dados_atualizados)

        if missing:
            return {
                "tipo": "coleta_dados",
                "cenario": scenario,
                "resposta": "Ainda preciso de algumas informações para definir o tratamento:",
                "perguntas": missing,
                "dados_clinicos": dados_atualizados,
            }

        protocolo = self.protocol_engine.get_protocol(scenario)

        if not protocolo:
            return {
                "tipo": "erro",
                "cenario": scenario,
                "resposta": "Não encontrei protocolo para esse cenário.",
                "dados_clinicos": dados_atualizados,
            }

        resposta_formatada = self._format_protocol(scenario, protocolo, dados_atualizados)

        return {
            "tipo": "protocolo_definido",
            "cenario": scenario,
            "resposta": resposta_formatada,
            "dados_clinicos": dados_atualizados,
        }

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""

        text = text.strip().lower()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _contains_any(self, text: str, terms: list[str]) -> bool:
        return any(term in text for term in terms)

    def _is_worsening_message(self, normalized_text: str) -> bool:
        worsening_terms = [
            "piora",
            "nao melhorou",
            "sem melhora",
            "piorou",
            "sem resposta ao tratamento",
            "falha terapeutica",
        ]
        return self._contains_any(normalized_text, worsening_terms)

    def _extract_age(self, normalized_text: str):
        match = re.search(r"\b(\d+)\s*anos?\b", normalized_text)
        if match:
            return int(match.group(1))
        return None

    def _extract_weight(self, normalized_text: str):
        match = re.search(r"\b(\d+)\s*kg\b", normalized_text)
        if match:
            return int(match.group(1))
        return None

    def _extract_allergy(self, normalized_text: str):
        negative_terms = [
            "sem alergia",
            "sem alergias",
            "sem alerg",
            "nega alergia",
            "nega alergias",
            "nega alerg",
            "nao tem alergia",
            "nao possui alergia",
            "sem alergia a penicilina",
            "nega alergia a penicilina",
            "sem alergia penicilina",
            "sem alergia a penicilinas",
            "sem alergia a antibioticos beta lactamicos",
        ]

        positive_terms = [
            "alergia a penicilina",
            "alergico a penicilina",
            "alergica a penicilina",
            "tem alergia",
            "possui alergia",
            "alergia",
            "alergico",
            "alergica",
        ]

        if self._contains_any(normalized_text, negative_terms):
            return False

        if self._contains_any(normalized_text, positive_terms):
            return True

        return None

    def _extract_severity(self, normalized_text: str):
        negative_terms = [
            "sem gravidade",
            "sem sinais de gravidade",
            "sem sinal de gravidade",
            "sem febre",
            "afebril",
            "sem toxemia",
            "dor leve",
            "sem dor intensa",
            "bom estado geral",
            "sem sinais de alarme",
            "sem sinais de alerta",
            "quadro leve",
            "quadro sem gravidade",
            "nao grave",
            "sem sinais sistemicos",
            "sem sinais sistêmicos",
        ]

        positive_terms = [
            "febre alta",
            "toxemia",
            "prostrado",
            "prostracao",
            "dor intensa",
            "mal estado geral",
            "sinais de gravidade",
            "grave",
            "quadro grave",
            "toxico",
            "toxico",
        ]

        if self._contains_any(normalized_text, negative_terms):
            return False

        if self._contains_any(normalized_text, positive_terms):
            return True

        return None

    def _extract_clinical_data(self, text: str):
        normalized_text = self._normalize_text(text)

        return {
            "idade": self._extract_age(normalized_text),
            "peso": self._extract_weight(normalized_text),
            "alergia": self._extract_allergy(normalized_text),
            "gravidade": self._extract_severity(normalized_text),
        }

    def _get_missing_questions(self, perguntas_protocolo: list[str], dados: dict):
        missing = []

        if perguntas_protocolo:
            for pergunta in perguntas_protocolo:
                pergunta_normalizada = self._normalize_text(pergunta)

                if "idade" in pergunta_normalizada or "anos" in pergunta_normalizada:
                    if dados.get("idade") is None:
                        missing.append(pergunta)
                    continue

                if (
                    "gravidade" in pergunta_normalizada
                    or "febre alta" in pergunta_normalizada
                    or "dor intensa" in pergunta_normalizada
                    or "toxemia" in pergunta_normalizada
                    or "sinais de alarme" in pergunta_normalizada
                    or "sinais de alerta" in pergunta_normalizada
                ):
                    if dados.get("gravidade") is None:
                        missing.append(pergunta)
                    continue

                if "alerg" in pergunta_normalizada or "penicilina" in pergunta_normalizada:
                    if dados.get("alergia") is None:
                        missing.append(pergunta)
                    continue

            return missing

        if dados.get("idade") is None:
            missing.append("Qual a idade do paciente?")

        if dados.get("gravidade") is None:
            missing.append("Há sinais de gravidade, como febre alta, dor intensa ou toxemia?")

        if dados.get("alergia") is None:
            missing.append("O paciente tem alergia à penicilina?")

        return missing

    def _format_protocol(self, scenario, protocolo, dados):
        linhas = []

        linhas.append("Avaliação Clínica:")
        linhas.append(f"Diagnóstico provável: {scenario.replace('_', ' ').title()}")
        linhas.append("")

        tratamento = protocolo.get("tratamento", {})
        primeira = tratamento.get("primeira_linha")
        alergia_alt = tratamento.get("alergia_penicilina")

        med = alergia_alt if dados.get("alergia") is True and alergia_alt else primeira

        if not med:
            return "Protocolo sem medicação configurada."

        linhas.append("Conduta recomendada:")
        linhas.append(f"Medicação: {med.get('medicamento', 'Não informado')}")
        linhas.append(f"Dose: {med.get('apresentacao', '')}".strip())
        linhas.append(
            f"Duração: {med.get('posologia', 'Não informada')} por {med.get('duracao', 'Não informada')}"
        )
        linhas.append("")
        linhas.append(f"Justificativa: {med.get('justificativa', 'Não informada')}")
        linhas.append("")

        quantidade_total = med.get("quantidade_total")
        if quantidade_total:
            linhas.append(f"Observações clínicas: Quantidade total: {quantidade_total}")

        return "\n".join(linhas)
