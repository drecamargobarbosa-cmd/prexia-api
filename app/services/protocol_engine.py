from typing import Dict


class ProtocolEngine:
    """
    Motor de protocolos clínicos estruturados.

    Cobre:
    - otite média aguda
    - faringoamigdalite
    - sinusite

    Responsabilidade:
    - receber contexto legado com cenário + dados clínicos
    - devolver recomendação terapêutica estruturada
    """

    def __init__(self) -> None:
        self.protocols = {
            "otite_media_aguda": self._otitis_protocol,
            "faringoamigdalite": self._pharyngotonsillitis_protocol,
            "sinusite": self._sinusitis_protocol,
        }

    def apply_protocol(self, context: dict) -> dict:
        """
        Ponto de entrada chamado pelo ClinicalEngine.
        Recebe o contexto legado e delega ao handler correto.
        """
        scenario = context.get("scenario")
        dados_clinicos = context.get("dados_clinicos", {})
        return self.generate_recommendation(scenario, dados_clinicos)

    def generate_recommendation(self, scenario: str, dados_clinicos: Dict) -> Dict:
        if not scenario:
            return self._fallback_no_scenario(dados_clinicos)

        handler = self.protocols.get(scenario)
        if not handler:
            return self._fallback_unknown_scenario(scenario, dados_clinicos)

        return handler(dados_clinicos)

    def _otitis_protocol(self, dados: Dict) -> Dict:
        idade = dados.get("idade")
        peso = dados.get("peso")
        alergia = dados.get("alergia")
        febre = dados.get("febre")
        dor_intensa = dados.get("dor_intensa")
        secrecao = dados.get("secrecao_auricular")
        toxemia = dados.get("toxemia")
        prostracao = dados.get("prostracao")
        duracao = dados.get("duracao_dias")

        gravidade = any(v is True for v in [dor_intensa, toxemia, prostracao])
        avaliacao = self._build_otitis_assessment(dados)

        if (
            duracao is not None and duracao < 3 and
            gravidade is False and
            febre is not True and
            secrecao is not True
        ):
            return {
                "resposta": self._build_structured_text(
                    avaliacao_clinica=avaliacao,
                    diagnostico_provavel="Quadro compatível com otite média aguda sem critérios fortes para antibioticoterapia imediata.",
                    conduta_recomendada="Considerar manejo sintomático inicial, analgesia e reavaliação clínica conforme evolução.",
                    justificativa="Quadros iniciais, sem sinais de maior gravidade, febre relevante ou otorreia, podem ser acompanhados clinicamente.",
                    observacoes_clinicas="Orientar retorno se houver piora da dor, febre, secreção auricular, prostração ou ausência de melhora."
                ),
                "conduta": {"cenario": "otite_media_aguda", "dados_clinicos": dados, "tipo": "observacao"}
            }

        if alergia is True:
            if idade is not None and idade >= 12:
                medicacao, dose, posologia, duracao_txt = "Azitromicina", "500 mg", "1 vez ao dia", "5 dias"
            else:
                if peso is None:
                    return self._missing_weight_response("otite_media_aguda", dados)
                medicacao, dose, posologia, duracao_txt = "Azitromicina", "10 mg/kg/dia", "1 vez ao dia", "5 dias"

            return self._build_protocol_response(
                scenario="otite_media_aguda", dados=dados, avaliacao=avaliacao,
                diagnostico="Quadro compatível com otite média aguda com alergia à penicilina.",
                conduta="Considerar antibiótico alternativo, analgesia e reavaliação clínica.",
                medicacao=medicacao, dose=dose, posologia=posologia, duracao=duracao_txt,
                justificativa="Há suporte clínico para tratamento antimicrobiano e a alergia à penicilina direciona a escolha para alternativa terapêutica.",
                observacoes="Reavaliar se houver piora clínica, manutenção de febre, otorreia persistente ou comprometimento do estado geral."
            )

        if idade is not None and idade >= 12:
            if gravidade or secrecao is True:
                medicacao, dose, posologia, duracao_txt = "Amoxicilina + Clavulanato", "875/125 mg", "12/12 horas", "7 a 10 dias"
                justificativa = "Em adulto com otite média aguda e sinais de maior gravidade ou otorreia, pode-se ampliar cobertura."
                diagnostico = "Quadro compatível com otite média aguda com sinais de maior gravidade."
            else:
                medicacao, dose, posologia, duracao_txt = "Amoxicilina", "500 mg", "8/8 horas", "7 dias"
                justificativa = "Em adulto sem alergia à penicilina, a amoxicilina é opção de primeira linha."
                diagnostico = "Quadro compatível com otite média aguda."

            return self._build_protocol_response(
                scenario="otite_media_aguda", dados=dados, avaliacao=avaliacao,
                diagnostico=diagnostico,
                conduta="Considerar antibioticoterapia, analgesia e reavaliação clínica.",
                medicacao=medicacao, dose=dose, posologia=posologia, duracao=duracao_txt,
                justificativa=justificativa,
                observacoes="Monitorar dor, febre, secreção auricular e estado geral. Reavaliar precocemente se houver piora."
            )

        if idade is not None and idade < 12:
            if peso is None:
                return self._missing_weight_response("otite_media_aguda", dados)

            if gravidade or secrecao is True:
                medicacao, dose, posologia, duracao_txt = "Amoxicilina + Clavulanato", "80 a 90 mg/kg/dia (componente amoxicilina)", "dividida em 2 tomadas ao dia", "10 dias"
                justificativa = "Em pediatria com sinais de maior gravidade ou otorreia, pode-se considerar ampliação de cobertura."
            else:
                medicacao, dose, posologia, duracao_txt = "Amoxicilina", "50 mg/kg/dia", "dividida em 2 a 3 tomadas ao dia", "7 a 10 dias"
                justificativa = "Em paciente pediátrico sem sinais maiores de gravidade, amoxicilina é opção de primeira linha."

            return self._build_protocol_response(
                scenario="otite_media_aguda", dados=dados, avaliacao=avaliacao,
                diagnostico="Quadro compatível com otite média aguda em pediatria.",
                conduta="Considerar antibioticoterapia conforme peso, analgesia e acompanhamento clínico.",
                medicacao=medicacao, dose=dose, posologia=posologia, duracao=duracao_txt,
                justificativa=justificativa,
                observacoes="Ajustar dose conforme apresentação disponível e peso. Reavaliar se houver piora clínica."
            )

        return self._fallback_incomplete_protocol("otite_media_aguda", dados)

    def _pharyngotonsillitis_protocol(self, dados: Dict) -> Dict:
        idade = dados.get("idade")
        peso = dados.get("peso")
        alergia = dados.get("alergia")
        febre = dados.get("febre")
        placas = dados.get("placas_amigdalianas")
        dor_garganta = dados.get("dor_garganta")
        toxemia = dados.get("toxemia")
        prostracao = dados.get("prostracao")

        gravidade = any(v is True for v in [toxemia, prostracao])
        avaliacao = self._build_pharyngotonsillitis_assessment(dados)

        if (
            dor_garganta is True and
            febre is not True and
            placas is not True and
            gravidade is False
        ):
            return {
                "resposta": self._build_structured_text(
                    avaliacao_clinica=avaliacao,
                    diagnostico_provavel="Quadro compatível com dor de garganta sem critérios fortes para etiologia bacteriana.",
                    conduta_recomendada="Considerar manejo sintomático inicial, analgesia, hidratação e reavaliação clínica.",
                    justificativa="Na ausência de febre, exsudato ou sinais sistêmicos, o quadro pode ser viral e não requer antibiótico inicial.",
                    observacoes_clinicas="Orientar retorno se houver piora, persistência, prostração importante, dificuldade para deglutir ou febre."
                ),
                "conduta": {"cenario": "faringoamigdalite", "dados_clinicos": dados, "tipo": "observacao"}
            }

        if alergia is True:
            if idade is not None and idade >= 12:
                medicacao, dose, posologia, duracao_txt = "Azitromicina", "500 mg", "1 vez ao dia", "5 dias"
            else:
                if peso is None:
                    return self._missing_weight_response("faringoamigdalite", dados)
                medicacao, dose, posologia, duracao_txt = "Azitromicina", "12 mg/kg/dia", "1 vez ao dia", "5 dias"

            return self._build_protocol_response(
                scenario="faringoamigdalite", dados=dados, avaliacao=avaliacao,
                diagnostico="Quadro compatível com faringoamigdalite com alergia à penicilina.",
                conduta="Considerar antibiótico alternativo, analgesia e reavaliação clínica.",
                medicacao=medicacao, dose=dose, posologia=posologia, duracao=duracao_txt,
                justificativa="Há elementos clínicos compatíveis com quadro infeccioso de garganta e alergia à penicilina.",
                observacoes="Reavaliar se houver piora clínica, dificuldade para deglutir, prostração importante ou falta de resposta."
            )

        criterio_bacteriano = (febre is True and placas is True) or gravidade

        if not criterio_bacteriano:
            return {
                "resposta": self._build_structured_text(
                    avaliacao_clinica=avaliacao,
                    diagnostico_provavel="Quadro ainda não característico de faringoamigdalite bacteriana.",
                    conduta_recomendada="Manter acompanhamento clínico e tratamento sintomático. Reavaliar evolução antes de iniciar antibiótico.",
                    justificativa="Não há critérios clínicos suficientes neste momento para indicar antibioticoterapia.",
                    observacoes_clinicas="Orientar retorno se houver piora, febre persistente, placas, prostração importante ou dificuldade para deglutir."
                ),
                "conduta": {"cenario": "faringoamigdalite", "dados_clinicos": dados, "tipo": "observacao"}
            }

        if idade is not None and idade >= 12:
            medicacao, dose, posologia, duracao_txt = "Amoxicilina", "500 mg", "8/8 horas", "10 dias"
        else:
            if peso is None:
                return self._missing_weight_response("faringoamigdalite", dados)
            medicacao, dose, posologia, duracao_txt = "Amoxicilina", "50 mg/kg/dia", "dividida em 2 a 3 tomadas ao dia", "10 dias"

        return self._build_protocol_response(
            scenario="faringoamigdalite", dados=dados, avaliacao=avaliacao,
            diagnostico="Quadro compatível com faringoamigdalite com provável etiologia bacteriana.",
            conduta="Considerar antibioticoterapia, analgesia, hidratação e acompanhamento clínico.",
            medicacao=medicacao, dose=dose, posologia=posologia, duracao=duracao_txt,
            justificativa="A presença de febre e placas aumenta a plausibilidade de infecção bacteriana de garganta.",
            observacoes="Monitorar dor, febre, estado geral e capacidade de ingestão oral. Reavaliar se houver piora."
        )

    def _sinusitis_protocol(self, dados: Dict) -> Dict:
        idade = dados.get("idade")
        peso = dados.get("peso")
        alergia = dados.get("alergia")
        duracao = dados.get("duracao_dias")
        febre = dados.get("febre")
        dor_facial = dados.get("dor_facial")
        secrecao = dados.get("secrecao_nasal_purulenta")
        toxemia = dados.get("toxemia")
        prostracao = dados.get("prostracao")

        gravidade = any(v is True for v in [toxemia, prostracao])
        avaliacao = self._build_sinusitis_assessment(dados)

        if duracao is not None and duracao < 10 and not gravidade:
            return {
                "resposta": self._build_structured_text(
                    avaliacao_clinica=avaliacao,
                    diagnostico_provavel="Quadro sugestivo de rinossinusite aguda provavelmente viral.",
                    conduta_recomendada="Não há indicação inicial de antibioticoterapia. Recomenda-se tratamento sintomático e reavaliação clínica.",
                    justificativa="Quadros com menos de 10 dias de evolução, sem sinais de gravidade, são mais frequentemente virais e autolimitados.",
                    observacoes_clinicas="Orientar retorno se houver piora, persistência por mais de 10 dias ou surgimento de sinais de gravidade."
                ),
                "conduta": {"cenario": "sinusite", "dados_clinicos": dados, "tipo": "expectante"}
            }

        criterio_bacteriano = (
            (duracao is not None and duracao >= 10) or
            (febre is True and dor_facial is True) or
            (secrecao is True and dor_facial is True)
        )

        if not criterio_bacteriano:
            return {
                "resposta": self._build_structured_text(
                    avaliacao_clinica=avaliacao,
                    diagnostico_provavel="Quadro ainda não característico de sinusite bacteriana.",
                    conduta_recomendada="Manter acompanhamento clínico e tratamento sintomático. Reavaliar evolução antes de iniciar antibiótico.",
                    justificativa="Não há critérios clínicos suficientes neste momento para indicar antibioticoterapia."
                ),
                "conduta": {"cenario": "sinusite", "dados_clinicos": dados, "tipo": "observacao"}
            }

        if alergia is True:
            if idade is not None and idade >= 12:
                medicacao, dose, posologia, duracao_txt = "Azitromicina", "500 mg", "1 vez ao dia", "5 dias"
            else:
                if peso is None:
                    return self._missing_weight_response("sinusite", dados)
                medicacao, dose, posologia, duracao_txt = "Azitromicina", "10 mg/kg/dia", "1 vez ao dia", "5 dias"
        else:
            if idade is not None and idade >= 12:
                medicacao, dose, posologia, duracao_txt = "Amoxicilina + Clavulanato", "875/125 mg", "12/12 horas", "5 a 7 dias"
            else:
                if peso is None:
                    return self._missing_weight_response("sinusite", dados)
                medicacao, dose, posologia, duracao_txt = "Amoxicilina + Clavulanato", "45 mg/kg/dia", "dividida em 2 tomadas", "10 dias"

        return self._build_protocol_response(
            scenario="sinusite", dados=dados, avaliacao=avaliacao,
            diagnostico="Quadro compatível com sinusite bacteriana.",
            conduta="Indicar antibioticoterapia e acompanhamento clínico.",
            medicacao=medicacao, dose=dose, posologia=posologia, duracao=duracao_txt,
            justificativa="Critérios clínicos compatíveis com sinusite bacteriana foram identificados.",
            observacoes="Reavaliar resposta ao tratamento e orientar retorno em caso de piora."
        )

    def _build_protocol_response(
        self, scenario, dados, avaliacao, diagnostico, conduta,
        medicacao, dose, posologia, duracao, justificativa, observacoes
    ) -> Dict:
        resposta = self._build_structured_text(
            avaliacao_clinica=avaliacao,
            diagnostico_provavel=diagnostico,
            conduta_recomendada=conduta,
            medicacao=medicacao,
            dose=dose,
            posologia=posologia,
            duracao=duracao,
            justificativa=justificativa,
            observacoes_clinicas=observacoes,
            prescricao=self._build_prescription_text(medicacao, dose, posologia, duracao)
        )

        return {
            "resposta": resposta,
            "diagnostico": diagnostico,
            "conduta": conduta,
            "medicacao": medicacao,
            "dose": dose,
            "posologia": posologia,
            "duracao": duracao,
            "justificativa": justificativa
        }

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
        duracao: str = "",
        prescricao: str = ""
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
        if prescricao:
            sections.append(f"Prescrição:\n{prescricao}")

        return "\n\n".join(sections)

    def _build_prescription_text(self, medicacao, dose, posologia, duracao) -> str:
        return f"{medicacao} {dose}\nUsar conforme posologia: {posologia}, por {duracao}."

    def _build_otitis_assessment(self, dados: Dict) -> str:
        parts = []
        if dados.get("idade") is not None:
            parts.append(f"Paciente com {dados.get('idade')} anos")
        if dados.get("duracao_dias") is not None:
            parts.append(f"{dados.get('duracao_dias')} dias de evolução")
        parts.append(f"febre: {self._bool_label(dados.get('febre'))}")
        parts.append(f"dor intensa: {self._bool_label(dados.get('dor_intensa'))}")
        parts.append(f"secreção auricular: {self._bool_label(dados.get('secrecao_auricular'))}")
        parts.append(f"toxemia: {self._bool_label(dados.get('toxemia'))}")
        parts.append(f"prostração: {self._bool_label(dados.get('prostracao'))}")
        parts.append(f"alergia à penicilina: {self._bool_label(dados.get('alergia'))}")
        return "; ".join(parts) + "."

    def _build_pharyngotonsillitis_assessment(self, dados: Dict) -> str:
        parts = []
        if dados.get("idade") is not None:
            parts.append(f"Paciente com {dados.get('idade')} anos")
        if dados.get("duracao_dias") is not None:
            parts.append(f"{dados.get('duracao_dias')} dias de evolução")
        parts.append(f"febre: {self._bool_label(dados.get('febre'))}")
        parts.append(f"dor de garganta: {self._bool_label(dados.get('dor_garganta'))}")
        parts.append(f"placas/exsudato: {self._bool_label(dados.get('placas_amigdalianas'))}")
        parts.append(f"toxemia: {self._bool_label(dados.get('toxemia'))}")
        parts.append(f"prostração: {self._bool_label(dados.get('prostracao'))}")
        parts.append(f"alergia à penicilina: {self._bool_label(dados.get('alergia'))}")
        return "; ".join(parts) + "."

    def _build_sinusitis_assessment(self, dados: Dict) -> str:
        parts = []
        if dados.get("idade") is not None:
            parts.append(f"Paciente com {dados.get('idade')} anos")
        if dados.get("duracao_dias") is not None:
            parts.append(f"{dados.get('duracao_dias')} dias de evolução")
        parts.append(f"dor facial: {self._bool_label(dados.get('dor_facial'))}")
        parts.append(f"secreção nasal purulenta: {self._bool_label(dados.get('secrecao_nasal_purulenta'))}")
        parts.append(f"febre: {self._bool_label(dados.get('febre'))}")
        parts.append(f"toxemia: {self._bool_label(dados.get('toxemia'))}")
        parts.append(f"prostração: {self._bool_label(dados.get('prostracao'))}")
        parts.append(f"alergia à penicilina: {self._bool_label(dados.get('alergia'))}")
        return "; ".join(parts) + "."

    def _bool_label(self, value) -> str:
        if value is True:
            return "Sim"
        if value is False:
            return "Não"
        return "Não informado"

    def _missing_weight_response(self, scenario: str, dados: Dict) -> Dict:
        return {
            "resposta": "Preciso do peso do paciente para calcular a dose com segurança.",
            "conduta": {"cenario": scenario, "dados_clinicos": dados}
        }

    def _fallback_no_scenario(self, dados: Dict) -> Dict:
        return {
            "resposta": "Não consegui identificar o cenário clínico para aplicar protocolo nesta etapa.",
            "conduta": {"cenario": None, "dados_clinicos": dados}
        }

    def _fallback_unknown_scenario(self, scenario: str, dados: Dict) -> Dict:
        return {
            "resposta": "O cenário clínico foi identificado, mas ainda não existe protocolo estruturado implementado para essa condição.",
            "conduta": {"cenario": scenario, "dados_clinicos": dados}
        }

    def _fallback_incomplete_protocol(self, scenario: str, dados: Dict) -> Dict:
        return {
            "resposta": "Consegui estruturar o caso clínico, mas ainda faltam elementos para aplicar esse protocolo com segurança.",
            "conduta": {"cenario": scenario, "dados_clinicos": dados}
        }
