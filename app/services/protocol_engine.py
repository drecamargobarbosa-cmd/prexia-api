import re
import unicodedata
from typing import Dict, Optional, Tuple

from app.protocols.antibiotics import ANTIBIOTIC_PROTOCOLS


class ProtocolEngine:
    def __init__(self) -> None:
        self.protocol_groups = {
            "antibioticos": ANTIBIOTIC_PROTOCOLS
        }

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""

        text = text.strip().lower()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _contains_term(self, normalized_text: str, term: str) -> bool:
        normalized_term = self._normalize_text(term)
        if not normalized_term:
            return False

        pattern = rf"\b{re.escape(normalized_term)}\b"
        return re.search(pattern, normalized_text) is not None

    def _score_protocol_match(self, normalized_message: str, protocol_data: Dict) -> int:
        score = 0

        synonyms = protocol_data.get("sinonimos", [])
        symptoms = protocol_data.get("sintomas_chave", [])

        for synonym in synonyms:
            if self._contains_term(normalized_message, synonym):
                score += 10

        for symptom in symptoms:
            if self._contains_term(normalized_message, symptom):
                score += 4

        return score

    def identify_scenario(self, message: str) -> Optional[str]:
        normalized_message = self._normalize_text(message)

        if not normalized_message:
            return None

        best_key = None
        best_score = 0

        for protocol_key, protocol_data in ANTIBIOTIC_PROTOCOLS.items():
            score = self._score_protocol_match(normalized_message, protocol_data)

            protocol_name_guess = protocol_key.replace("_", " ")
            if self._contains_term(normalized_message, protocol_name_guess):
                score += 8

            if score > best_score:
                best_score = score
                best_key = protocol_key

        return best_key if best_score > 0 else None

    def get_protocol(self, scenario: str) -> Optional[Dict]:
        if not scenario:
            return None

        return ANTIBIOTIC_PROTOCOLS.get(scenario)

    def identify_group_and_protocol(self, message: str) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
        normalized_message = self._normalize_text(message)

        if not normalized_message:
            return None, None, None

        best_group = None
        best_protocol_key = None
        best_protocol = None
        best_score = 0

        for group_name, protocols in self.protocol_groups.items():
            for protocol_key, protocol_data in protocols.items():
                score = self._score_protocol_match(normalized_message, protocol_data)

                protocol_name_guess = protocol_key.replace("_", " ")
                if self._contains_term(normalized_message, protocol_name_guess):
                    score += 8

                if score > best_score:
                    best_score = score
                    best_group = group_name
                    best_protocol_key = protocol_key
                    best_protocol = protocol_data

        if best_score == 0:
            return None, None, None

        return best_group, best_protocol_key, best_protocol
