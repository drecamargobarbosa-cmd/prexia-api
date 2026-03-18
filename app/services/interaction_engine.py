def check_drug_interactions(message: str, recommended_antibiotic: str | None) -> list[str]:
    m = message.lower()
    alerts = []

    if not recommended_antibiotic:
        return alerts

    if "varfarina" in m and recommended_antibiotic.lower() in ["azitromicina", "ciprofloxacino", "levofloxacino"]:
        alerts.append(
            f"{recommended_antibiotic} pode alterar o efeito anticoagulante da varfarina. Monitorar INR e risco de sangramento."
        )

    if "metotrexato" in m and "amoxicilina" in recommended_antibiotic.lower():
        alerts.append(
            f"{recommended_antibiotic} pode aumentar toxicidade do metotrexato. Avaliar risco e monitorar."
        )

    return alerts


def check_disease_interactions(message: str, recommended_antibiotic: str | None) -> list[str]:
    m = message.lower()
    alerts = []

    if not recommended_antibiotic:
        return alerts

    if ("doença renal" in m or "doenca renal" in m or "insuficiência renal" in m or "insuficiencia renal" in m) and recommended_antibiotic.lower() in [
        "nitrofurantoína", "nitrofurantoina", "ciprofloxacino", "amoxicilina", "amoxicilina + clavulanato"
    ]:
        alerts.append(
            "Considerar avaliação de função renal para ajuste de dose ou adequação da escolha antibiótica."
        )

    if "gestante" in m or "gestação" in m or "gestacao" in m:
        alerts.append(
            "Confirmar segurança do antibiótico no contexto gestacional e idade gestacional."
        )

    return alerts
