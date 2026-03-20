from app.protocols.antibiotics import ANTIBIOTIC_PROTOCOLS


class ProtocolEngine:
    def load_protocol(self, scenario: str) -> dict | None:
        if not scenario:
            return None

        return ANTIBIOTIC_PROTOCOLS.get(scenario)

    def list_available_protocols(self) -> list[str]:
        return list(ANTIBIOTIC_PROTOCOLS.keys())

    def identify_scenario(self, question: str) -> str | None:
        if not question:
            return None

        question_normalized = question.lower()

        for scenario, protocol in ANTIBIOTIC_PROTOCOLS.items():
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
            "usar_alternativa": False,
        }

        if dados_clinicos.get("alergia") is True and protocol.get("alergia_penicilina"):
            protocolo_resultado["usar_alternativa"] = True

        return protocolo_resultado
