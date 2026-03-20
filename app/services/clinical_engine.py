from app.protocols.antibiotics import ANTIBIOTIC_PROTOCOLS


class ProtocolEngine:
    def __init__(self):
        self.protocols = {
            "antibioticos": ANTIBIOTIC_PROTOCOLS,
        }

    def load_protocol(self, scenario: str) -> dict | None:
        if not scenario:
            return None

        for grupo in self.protocols.values():
            if scenario in grupo:
                return grupo.get(scenario)

        return None

    def list_available_protocols(self) -> list[str]:
        all_protocols = []

        for grupo in self.protocols.values():
            all_protocols.extend(grupo.keys())

        return all_protocols

    def identify_scenario(self, question: str) -> str | None:
        if not question:
            return None

        question_normalized = question.lower()

        for grupo in self.protocols.values():
            for scenario, protocol in grupo.items():
                keywords = protocol.get("keywords", [])

                for keyword in keywords:
                    if keyword.lower() in question_normalized:
                        return scenario

        return None

    def get_protocol(self, scenario: str, dados_clinicos: dict | None = None) -> dict | None:
        protocol = self.load_protocol(scenario)

        if not protocol:
            return None

        dados_clinicos = dados_clinicos or {}

        protocolo_resultado = {
            "primeira_linha": protocol.get("primeira_linha"),
            "alergia_penicilina": protocol.get("alergia_penicilina"),
            "alternativa": protocol.get("alternativa"),
            "observacoes": protocol.get("observacoes", []),
        }

        return protocolo_resultado
