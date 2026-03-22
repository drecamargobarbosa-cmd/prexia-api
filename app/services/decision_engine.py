from app.services.protocol_engine import ProtocolEngine
from app.services.interaction_engine import (
    check_drug_interactions,
    check_disease_interactions
)


class DecisionEngine:
    """
    Camada de decisão terapêutica.

    Responsabilidades:
    - receber contexto clínico já estruturado
    - decidir qual resposta terapêutica gerar
    - consultar protocolos quando houver suporte
    - anexar alertas de interação
    - devolver resposta pronta para o frontend

    Não faz extração de dados nem detecção de cenário.
    """

    def __init__(self):
        self.protocol_engine = ProtocolEngine()
        self.check_drug_interactions = check_drug_interactions
        self.check_disease_interactions = check_disease_interactions

    def decide(self, question: str, context: dict) -> dict:
        scenario = context.get("scenario")
        dados = context.get("dados_clinicos", {})
        intent = context.get("intent", "geral")

        protocol_result = self._generate_protocol_response(scenario, dados)

        resposta = protocol_result.get("resposta", "Conduta definida.")
        medicacao = self._extract_medication_from_protocol_result(protocol_result)

        drug_alerts = self.check_drug_interactions(question, medicacao)
        disease_alerts = self.check_disease_interactions(question, medicacao)
        alertas = drug_alerts + disease_alerts

        if alertas:
            resposta = resposta + "\n\nAtenção:\n" + "\n".join(f"• {a}" for a in alertas)

        response_type = self._resolve_response_type(intent)

        return {
            "resposta": resposta,
            "clinical_response": {
                "tipo": response_type,
                "cenario": scenario,
                "resposta": resposta,
                "dados_clinicos": dados,
                "alertas": alertas
            }
        }

    def _resolve_response_type(self, intent: str) -> str:
        if intent in ["tratamento", "antibiotico", "medicamento", "dose", "geral"]:
            return "tratamento"
        return "conduta"

    def _extract_medication_from_protocol_result(self, protocol_result: dict):
        if not isinstance(protocol_result, dict):
            return None

        if protocol_result.get("medicacao"):
            return protocol_result.get("medicacao")

        conduta = protocol_result.get("conduta")
        if isinstance(conduta, dict):
            return conduta.get("medicacao")

        clinical_response = protocol_result.get("clinical_response")
        if isinstance(clinical_response, dict):
            return clinical_response.get("medicacao")

        return None

    def _generate_protocol_response(self, scenario: str, dados: dict) -> dict:
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
            return {
                "resposta": (
                    "Consegui estruturar o caso clínico, mas não há protocolo específico implementado "
                    "ou o motor de protocolo não conseguiu gerar a recomendação nesta etapa."
                ),
                "conduta": {
                    "cenario": scenario,
                    "dados_clinicos": dados
                }
            }
