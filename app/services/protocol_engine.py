from typing import Dict, Optional


class ProtocolEngine:
    """
    Motor de protocolos clínicos estruturados.

    Nesta etapa, cobre:
    - otite média aguda
    - faringoamigdalite
    - sinusite

    Responsabilidade:
    - receber cenário + dados clínicos já organizados
    - devolver recomendação terapêutica estruturada
    """

    def __init__(self) -> None:
        self.protocols = {
            "otite_media_aguda": self._otitis_protocol,
            "faringoamigdalite": self._pharyngotonsillitis_protocol,
            "sinusite": self._sinusitis_protocol,
        }

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

        gravidade = any(v is True for v in [dor_intensa, toxemia, prostracao])

        avaliacao = self._build_otitis_assessment(dados)

        if alergia is True:
            if idade is not None and idade >= 12:
                medicacao = "Azitromicina"
                dose = "500 mg"
                posologia = "1 vez ao dia"
                duracao = "5 dias"
            else:
                medicacao = "Azitromicina"
                dose = "10 mg/kg/dia"
                posologia = "1 vez ao dia"
                duracao = "5 dias"

            diagnostico = "Quadro compatível com otite média aguda com alergia à penicilina."
            conduta = (
                "Considerar antibiótico alternativo, analgesia e reavaliação clínica conforme evolução."
            )
            justificativa = (
                "Há suporte clínico para tratamento antimicrobiano e a alergia à penicilina direciona a escolha para alternativa terapêutica."
            )

            return self._build_protocol_response(
                scenario="otite_media_aguda",
                dados=dados,
                avaliacao=avaliacao,
                diagnostico=diagnostico,
                conduta=conduta,
                medicacao=medicacao,
                dose=dose,
                posologia=posologia,
                duracao=duracao,
                justificativa=justificativa,
                observacoes=(
                    "Reavaliar se houver piora clínica, manutenção de febre, otorreia persistente ou comprometimento do estado geral."
                )
            )

        if idade is not None and idade >= 12:
            if gravidade:
                medicacao = "Amoxicilina + Clavulanato"
                dose = "875/125 mg"
                posologia = "12/12 horas"
                duracao = "7 a 10 dias"
                justificativa = (
                    "Em adulto com quadro compatível com otite média aguda e sinais de maior gravidade, pode-se ampliar cobertura."
                )
            else:
                medicacao = "Amoxicilina"
                dose = "500 mg"
                posologia = "8/8 horas"
                duracao = "7 dias"
                justificativa = (
                    "Em adulto sem alergia à penicilina, a amoxicilina é opção de primeira linha."
                )

            diagnostico = (
                "Quadro compatível com otite média aguda com sinais de maior gravidade."
                if gravidade else
                "Quadro compatível com otite média aguda sem sinais maiores de gravidade."
            )

            conduta = (
                "Indicar antibioticoterapia, analgesia e reavaliação clínica."
            )

            return self._build_protocol_response(
                scenario="otite_media_aguda",
                dados=dados,
                avaliacao=avaliacao,
                diagnostico=diagnostico,
                conduta=conduta,
                medicacao=medicacao,
                dose=dose,
                posologia=posologia,
                duracao=duracao,
                justificativa=justificativa,
                observacoes=(
                    "Monitorar dor, febre, secreção auricular e estado geral. Reavaliar precocemente se houver piora."
                )
            )

        if idade is not None and idade < 12:
            if peso is None:
                return self._missing_weight_response(
                    scenario="otite_media_aguda",
                    dados=dados
                )

            if gravidade:
                medicacao = "Amoxicilina + Clavulanato"
                dose = "80 a 90 mg/kg/dia (componente amoxicilina)"
                posologia = "dividida em 2 tomadas ao dia"
                duracao = "10 dias"
                justificativa = (
                    "Em pediatria com sinais de maior gravidade, pode-se considerar ampliação de cobertura."
                )
            else:
                medicacao = "Amoxicilina"
                dose = "50 mg/kg/dia"
                posologia = "dividida em 2 a 3 tomadas ao dia"
                duracao = "7 a 10 dias"
                justificativa = (
                    "Em paciente pediátrico sem gravidade, amoxicilina é opção de primeira linha."
                )

            diagnostico = (
                "Quadro compatível com otite média aguda em pediatria com sinais de maior gravidade."
                if gravidade else
                "Quadro compatível com otite média aguda em pediatria sem sinais maiores de gravidade."
            )

            conduta = (
                "Indicar antibioticoterapia conforme peso, analgesia e acompanhamento clínico."
            )

            return self._build_protocol_response(
                scenario="otite_media_aguda",
                dados=dados,
                avaliacao=avaliacao,
                diagnostico=diagnostico,
                conduta=conduta,
                medicacao=medicacao,
                dose=dose,
                posologia=posologia,
                duracao=duracao,
                justificativa=justificativa,
                observacoes=(
                    "Ajustar dose conforme apresentação disponível e peso. Reavaliar se houver piora clínica."
                )
            )

        return self._fallback_incomplete_protocol(
            scenario="otite_media_aguda",
            dados=dados
        )

    def _pharyngotonsillitis_protocol(self, dados: Dict) -> Dict:
        idade = dados.get("idade")
        peso = dados.get("peso")
        alergia = dados.get("alergia")
        febre = dados.get("febre")
        placas = dados.get("placas_amigdalianas")
        toxemia = dados.get("toxemia")
        prostracao = dados.get("prostracao")

        gravidade = any(v is True for v in [toxemia, prostracao])

        avaliacao = self._build_pharyngotonsillitis_assessment(dados)

        if alergia is True:
            if idade is not None and idade >= 12:
                medicacao = "Azitromicina"
                dose = "500 mg"
                posologia = "1 vez ao dia"
                duracao = "5 dias"
            else:
                if peso is None:
                    return self._missing_weight_response(
                        scenario="faringoamigdalite",
                        dados=dados
                    )
                medicacao = "Azitromicina"
                dose = "12 mg/kg/dia"
                posologia = "1 vez ao dia"
                duracao = "5 dias"

            diagnostico = "Quadro compatível com faringoamigdalite com alergia à penicilina."
            conduta = "Considerar antibiótico alternativo, analgesia e reavaliação clínica."
            justificativa = (
                "Há elementos clínicos compatíveis com quadro infeccioso de garganta e alergia à penicilina."
            )

            return self._build_protocol_response(
                scenario="faringoamigdalite",
                dados=dados,
                avaliacao=avaliacao,
                diagnostico=diagnostico,
                conduta=conduta,
                medicacao=medicacao,
                dose=dose,
                posologia=posologia,
                duracao=duracao,
                justificativa=justificativa,
                observacoes=(
                    "Reavaliar se houver piora clínica, dificuldade para deglutir, prostração importante ou falta de resposta."
                )
            )

        if idade is not None and idade >= 12:
            medicacao = "Amoxicilina"
            dose = "500 mg"
            posologia = "8/8 horas"
            duracao = "10 dias"
        else:
            if peso is None:
                return self._missing_weight_response(
                    scenario="faringoamigdalite",
                    dados=dados
                )
            medicacao = "Amoxicilina"
            dose = "50 mg/kg/dia"
            posologia = "dividida em 2 a 3 tomadas ao dia"
            duracao = "10 dias"

        diagnostico = (
            "Quadro compatível com faringoamigdalite com sinais de maior gravidade."
            if gravidade else
            "Quadro compatível com faringoamigdalite."
        )

        conduta = (
            "Considerar antibioticoterapia, analgesia, hidratação e acompanhamento clínico."
        )

        justificativa = (
            "A presença de febre e placas/exsudato aumenta a plausibilidade de infecção bacteriana de garganta."
            if febre is True and placas is True else
            "O conjunto clínico permite considerar conduta antimicrobiana conforme protocolo."
        )

        return self._build_protocol_response(
            scenario="faringoamigdalite",
            dados=dados,
            avaliacao=avaliacao,
            diagnostico=diagnostico,
            conduta=conduta,
            medicacao=medicacao,
            dose=dose,
            posologia=posologia,
            duracao=duracao,
            justificativa=justificativa,
            observacoes=(
                "Monitorar dor, febre, estado geral e capacidade de ingestão oral. Reavaliar se houver piora."
            )
        )

    def _sinusitis_protocol(self, dados: Dict) -> Dict:
        idade = dados.get("idade")
        peso = dados.get("peso")
        alergia = dados.get("alergia")
        toxemia = dados.get("toxemia")
        prostracao = dados.get("prostracao")

        gravidade = any(v is True for v in [toxemia, prostracao])

        avaliacao = self._build_sinusitis_assessment(dados)

        if alergia is True:
            if idade is not None and idade >= 12:
                medicacao = "Azitromicina"
                dose = "500 mg"
                posologia = "1 vez ao dia"
                duracao = "5 dias"
            else:
                if peso is None:
                    return self._missing_weight_response(
                        scenario="sinusite",
                        dados=dados
                    )
                medicacao = "Azitromicina"
                dose = "10 mg/kg/dia"
                posologia = "1 vez ao dia"
                duracao = "5 dias"

            diagnostico = "Quadro compatível com sinusite com alergia à penicilina."
            conduta = "Considerar antibiótico alternativo, medidas de suporte e reavaliação clínica."
            justificativa = (
                "Há critérios clínicos compatíveis com sinusite e a alergia à penicilina exige alternativa."
            )

            return self._build_protocol_response(
                scenario="sinusite",
                dados=dados,
                avaliacao=avaliacao,
                diagnostico=diagnostico,
                conduta=conduta,
                medicacao=medicacao,
                dose=dose,
                posologia=posologia,
                duracao=duracao,
                justificativa=justificativa,
                observacoes=(
                    "Reavaliar se houver piora, persistência importante dos sintomas ou sinais sistêmicos."
                )
            )

        if idade is not None and idade >= 12:
            if gravidade:
                medicacao = "Amoxicilina + Clavulanato"
                dose = "875/125 mg"
                posologia = "12/12 horas"
                duracao = "7 a 10 dias"
                justificativa = (
                    "Em adulto com quadro compatível com sinusite e maior gravidade, pode-se ampliar cobertura."
                )
            else:
                medicacao = "Amoxicilina + Clavulanato"
                dose = "875/125 mg"
                posologia = "12/12 horas"
                duracao = "5 a 7 dias"
                justificativa = (
                    "Em adulto com critérios clínicos para sinusite bacteriana, a associação com clavulanato é opção frequente."
                )
        else:
            if peso is None:
                return self._missing_weight_response(
                    scenario="sinusite",
                    dados=dados
                )

            medicacao = "Amoxicilina + Clavulanato"
            dose = "45 mg/kg/dia (componente amoxicilina)"
            posologia = "dividida em 2 tomadas ao dia"
            duracao = "10 dias"
            justificativa = (
                "Em pediatria, a decisão deve considerar peso e apresentação disponível."
            )

        diagnostico = (
            "Quadro compatível com sinusite com sinais de maior gravidade."
            if gravidade else
            "Quadro compatível com sinusite."
        )

        conduta = "Considerar antibioticoterapia, medidas sintomáticas e reavaliação clínica."

        return self._build_protocol_response(
            scenario="sinusite",
            dados=dados,
            avaliacao=avaliacao,
            diagnostico=diagnostico,
            conduta=conduta,
            medicacao=medicacao,
            dose=dose,
            posologia=posologia,
            duracao=duracao,
            justificativa=justificativa,
            observacoes=(
                "Monitorar febre, dor facial, secreção e evolução clínica. Reavaliar se não houver melhora."
            )
        )

    def _build_protocol_response(
        self,
        scenario: str,
        dados: Dict,
        avaliacao: str,
        diagnostico: str,
        conduta: str,
        medicacao: str,
        dose: str,
        posologia: str,
        duracao: str,
        justificativa: str,
        observacoes: str
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
            prescricao=self._build_prescription_text(
                medicacao=medicacao,
                dose=dose,
                posologia=posologia,
                duracao=duracao
            )
        )

        return {
            "resposta": resposta,
            "medicacao": medicacao,
            "dose": dose,
            "posologia": posologia,
            "duracao": duracao,
            "conduta": {
                "cenario": scenario,
                "dados_clinicos": dados,
                "medicacao": medicacao,
                "dose": dose,
                "posologia": posologia,
                "duracao": duracao
            }
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

    def _build_prescription_text(self, medicacao: str, dose: str, posologia: str, duracao: str) -> str:
        return (
            f"{medicacao} {dose}\n"
            f"Usar conforme posologia: {posologia}, por {duracao}."
        )

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
        resposta = "Preciso do peso do paciente para calcular a dose com segurança."
        return {
            "resposta": resposta,
            "conduta": {
                "cenario": scenario,
                "dados_clinicos": dados
            }
        }

    def _fallback_no_scenario(self, dados: Dict) -> Dict:
        return {
            "resposta": "Não consegui identificar o cenário clínico para aplicar protocolo nesta etapa.",
            "conduta": {
                "cenario": None,
                "dados_clinicos": dados
            }
        }

    def _fallback_unknown_scenario(self, scenario: str, dados: Dict) -> Dict:
        return {
            "resposta": (
                "O cenário clínico foi identificado, mas ainda não existe protocolo estruturado implementado para essa condição."
            ),
            "conduta": {
                "cenario": scenario,
                "dados_clinicos": dados
            }
        }

    def _fallback_incomplete_protocol(self, scenario: str, dados: Dict) -> Dict:
        return {
            "resposta": (
                "Consegui estruturar o caso clínico, mas ainda faltam elementos para aplicar esse protocolo com segurança."
            ),
            "conduta": {
                "cenario": scenario,
                "dados_clinicos": dados
            }
        }
