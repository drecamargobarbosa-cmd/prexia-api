from app.protocols.antibiotics import ANTIBIOTIC_PROTOCOLS


class ProtocolEngine:

    def load_protocol(self, scenario: str) -> dict | None:
        if not scenario:
            return None

        return ANTIBIOTIC_PROTOCOLS.get(scenario)

    def list_available_protocols(self) -> list[str]:
        return list(ANTIBIOTIC_PROTOCOLS.keys())
