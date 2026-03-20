def normalize(text: str) -> str:
    if not text:
        return ""

    return (
        text.lower()
        .strip()
        .replace("á", "a")
        .replace("à", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("ä", "a")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("ë", "e")
        .replace("í", "i")
        .replace("ì", "i")
        .replace("î", "i")
        .replace("ï", "i")
        .replace("ó", "o")
        .replace("ò", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ö", "o")
        .replace("ú", "u")
        .replace("ù", "u")
        .replace("û", "u")
        .replace("ü", "u")
        .replace("ç", "c")
    )


def compare_with_protocol(
    proposed: str | None,
    recommended: dict | None,
) -> dict:
    if not proposed or not recommended or not recommended.get("medicamento"):
        return {
            "conformidade_protocolo": "nao_avaliada",
            "confirmacao_necessaria": False,
            "alertas_protocolo": []
        }

    proposed_n = normalize(proposed)
    recommended_n = normalize(recommended["medicamento"])

    if proposed_n in recommended_n or recommended_n in proposed_n:
        return {
            "conformidade_protocolo": "dentro_do_protocolo",
            "confirmacao_necessaria": False,
            "alertas_protocolo": []
        }

    return {
        "conformidade_protocolo": "fora_do_protocolo",
        "confirmacao_necessaria": True,
        "alertas_protocolo": [
            f"A conduta proposta ({proposed}) nao corresponde a melhor indicacao inicial do protocolo.",
            f"Primeira sugestao protocolar: {recommended['medicamento']}."
        ]
    }
