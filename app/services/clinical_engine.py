from app.protocols.antibiotics import ANTIBIOTIC_PROTOCOLS


def detect_scenario(message: str) -> str | None:
    m = message.lower()

    if "sinusite" in m:
        return "sinusite_bacteriana"
    if "itu" in m or "infecção urinária" in m or "infeccao urinaria" in m or "cistite" in m:
        return "itu_nao_complicada"
    if "odontogenica" in m or "odontogênica" in m or "dente" in m or "odontologica" in m or "odontológica" in m:
        return "infeccao_odontogenica"

    return None


def has_penicillin_allergy(message: str) -> bool:
    m = message.lower()
    return "alergia a penicilina" in m or "alérgico a penicilina" in m or "alergico a penicilina" in m


def build_response(message: str) -> dict:
    scenario = detect_scenario(message)

    if not scenario:
        return {
            "resposta": (
                "Ainda não tenho protocolo estruturado para esse cenário. "
                "No momento consigo apoiar sinusite bacteriana, ITU não complicada e infecção odontogênica."
            ),
            "tipo": "fallback",
            "fonte": "motor_clinico_estruturado"
        }

    protocol = ANTIBIOTIC_PROTOCOLS[scenario]

    if has_penicillin_allergy(message) and "alergia_penicilina" in protocol:
        choice = protocol["alergia_penicilina"]
        motivo = "Escolha baseada em alergia a penicilina."
    else:
        choice = protocol["primeira_linha"]
        motivo = "Escolha de primeira linha segundo protocolo estruturado."

    observacoes = " ".join(protocol.get("observacoes", []))

    resposta = (
        f"Antibiótico sugerido: {choice['medicamento']}. "
        f"Dose: {choice['dose']}. "
        f"Duração: {choice['duracao']}. "
        f"{motivo} "
        f"Observações: {observacoes}"
    )

    return {
        "resposta": resposta,
        "tipo": "recomendacao_estruturada",
        "cenario": scenario,
        "fonte": "motor_clinico_estruturado"
    }
