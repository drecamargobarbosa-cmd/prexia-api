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
