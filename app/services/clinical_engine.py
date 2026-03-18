from app.services.protocol_engine import ProtocolEngine
from app.services.interaction_engine import InteractionEngine
from app.services.safety_engine import SafetyEngine
from app.services.response_engine import ResponseEngine


class ClinicalEngine:

    def __init__(self):

        self.protocol_engine = ProtocolEngine()
        self.interaction_engine = InteractionEngine()
        self.safety_engine = SafetyEngine()
        self.response_engine = ResponseEngine()

    def evaluate(self, question: str):

        # 1 entender cenário clínico
        scenario = self.interaction_engine.identify_scenario(question)

        # 2 carregar protocolo
        protocol = self.protocol_engine.load_protocol(scenario)

        # 3 aplicar validações de segurança
        safety_alerts = self.safety_engine.check(question)

        # 4 montar resposta
        response = self.response_engine.build_response(protocol, scenario)

        # 5 anexar alertas de segurança
        response["alertas_seguranca"] = safety_alerts

        return response
