def normalize(text: str) -> str:
    return (
        text.lower()
        .replace("á", "a")
        .replace("à", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )


def compare_with_protocol(proposed: str | None, recommended: dict | None) -> dict:
    if not proposed or not recommended:
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
            f"A conduta proposta ({proposed}) não corresponde à melhor indicação inicial do protocolo.",
            f"Primeira sugestão protocolar: {recommended['medicamento']}."
        ]
    }


def build_final_response(clinical_data: dict, drug_alerts: list[str], disease_alerts: list[str], safety_data: dict) -> dict:
    if not clinical_data["protocol_found"]:
        return {
            "resposta": clinical_data["justification"],
            "tipo": "fallback",
            "cenario": None,
            "antibiotico_sugerido": None,
            "dose": None,
            "duracao": None,
            "interacoes_medicamentosas": drug_alerts,
            "alertas_doencas": disease_alerts,
            "conformidade_protocolo": safety_data["conformidade_protocolo"],
            "confirmacao_necessaria": safety_data["confirmacao_necessaria"],
            "alertas_protocolo": safety_data["alertas_protocolo"],
            "fonte": "motor_clinico_refatorado"
        }

    recommended = clinical_data["recommended"]

    resposta = (
        f"Antibiótico sugerido: {recommended['medicamento']}. "
        f"Dose: {recommended['dose']}. "
        f"Duração: {recommended['duracao']}. "
        f"Justificativa: {clinical_data['justification']} "
        f"Observações: {' '.join(clinical_data.get('observacoes', []))}"
    )

    return {
        "resposta": resposta,
        "tipo": "recomendacao_estruturada",
        "cenario": clinical_data["scenario"],
        "antibiotico_sugerido": recommended["medicamento"],
        "dose": recommended["dose"],
        "duracao": recommended["duracao"],
        "interacoes_medicamentosas": drug_alerts,
        "alertas_doencas": disease_alerts,
        "conformidade_protocolo": safety_data["conformidade_protocolo"],
        "confirmacao_necessaria": safety_data["confirmacao_necessaria"],
        "alertas_protocolo": safety_data["alertas_protocolo"],
        "conduta_proposta": clinical_data["proposed"],
        "fonte": "motor_clinico_refatorado"
    }
