import json
from pathlib import Path


class ProtocolEngine:

    def __init__(self):

        self.protocol_path = Path(__file__).resolve().parent.parent / "protocols"


    def load_protocol(self, scenario):

        if not scenario:
            return None

        protocol_file = self.protocol_path / f"{scenario}.json"

        if not protocol_file.exists():
            return None

        with open(protocol_file, "r", encoding="utf-8") as f:

            protocol = json.load(f)

        return protocol
