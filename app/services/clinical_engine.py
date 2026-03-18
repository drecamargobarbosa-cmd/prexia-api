from app.protocols.infections import INFECTION_PROTOCOLS


def detect_scenario(message: str) -> str | None:
    m = message.lower()

    for scenario, data in INFECTION_PROTOCOLS.items():
        for keyword in data["keywords"]:
            if keyword in m:
                return scenario

    return None


def has_penicillin_allergy(message: str) -> bool:
    m = message.lower()
    triggers = [
        "alergia a penicilina",
        "alérgico a penicilina",
        "alergico a penicilina",
        "alergia penicilina"
    ]
    return any(t in m for t in triggers)


def extract_proposed_antibiotic(message: str) -> str | None:
    m = message.lower()

    known_antibiotics = [
        "amoxicilina",
        "amoxicilina + clavulanato",
        "amoxicilina clavulanato",
        "azitromicina",
        "clindamicina",
        "nitrofurantoína",
        "nitrofurantoina",
        "fosfomicina",
        "ciprofloxacino",
        "levofloxacino",
        "cefuroxima"
    ]

    trigger_phrases = [
        "estou pensando em usar",
        "pensei em usar",
        "quero usar",
        "vou usar",
        "usar",
        "prescrever",
        "sugiro",
        "sugerir"
    ]

    if any(trigger in m for trigger in trigger_phrases):
        for antibiotic in known_antibiotics:
            if antibiotic in m:
                return antibiotic

    return None


def recommend_antibiotic(message: str) -> dict:
    scenario = detect_scenario(message)

    if not scenario:
        return {
            "scenario": None,
            "recommended": None,
            "proposed": extract_proposed_antibiotic(message),
            "protocol_found": False,
            "justification": "Ainda não há protocolo estruturado para este cenário."
        }

    protocol = INFECTION_PROTOCOLS[scenario]
    penicillin_allergy = has_penicillin_allergy(message)

    if penicillin_allergy and "alergia_penicilina" in protocol:
        recommended = protocol["alergia_penicilina"]
        justification = "Escolha baseada em alergia a penicilina."
    else:
        recommended = protocol["primeira_linha"]
        justification = "Escolha de primeira linha segundo protocolo estruturado."

    return {
        "scenario": scenario,
        "recommended": recommended,
        "proposed": extract_proposed_antibiotic(message),
        "protocol_found": True,
        "justification": justification,
        "observacoes": protocol.get("observacoes", [])
    }
