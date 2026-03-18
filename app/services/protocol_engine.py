from app.protocols.antibiotics import ANTIBIOTIC_PROTOCOLS


class ProtocolEngine:

    def load_protocol(self, scenario: str):

        if not scenario:
            return None

        return ANTIBIOTIC_PROTOCOLS.get(scenario)
