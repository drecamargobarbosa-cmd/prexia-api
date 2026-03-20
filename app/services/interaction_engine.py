from app.services.safety_engine import normalize


def check_drug_interactions(message: str, recommended_antibiotic: str | None) -> list[str]:
    m = normalize(message)
    alerts = []

    if not recommended_antibiotic:
        return alerts

    antibiotic = normalize(recommended_antibiotic)

    if "varfarina" in m and antibiotic in ["azitromicina", "ciprofloxacino", "levofloxacino"]:
        alerts.append(
            f"{recommended_antibiotic} pode alterar o efeito anticoagulante da varfarina. Monitorar INR e risco de sangramento."
        )

    if "metotrexato" in m and "amoxicilina" in antibiotic:
        alerts.append(
            f"{recommended_antibiotic} pode aumentar a toxicidade do metotrexato. Avaliar risco clínico e monitorar."
        )

    if ("anticoncepcional" in m or "contraceptivo" in m or "pilula" in m or "pílula" in m) and antibiotic in [
        "azitromicina",
        "amoxicilina",
        "amoxicilina + clavulanato",
        "clindamicina",
        "ciprofloxacino",
        "levofloxacino",
        "nitrofurantoina",
        "nitrofurantoína",
    ]:
        alerts.append(
            "Orientar que episódios de vômitos, diarreia ou má absorção podem reduzir a eficácia do anticoncepcional oral."
        )

    return alerts


def check_disease_interactions(message: str, recommended_antibiotic: str | None) -> list[str]:
    m = normalize(message)
    alerts = []

    if not recommended_antibiotic:
        return alerts

    antibiotic = normalize(recommended_antibiotic)

    if (
        "doenca renal" in m
        or "doenca nos rins" in m
        or "insuficiencia renal" in m
        or "renal" in m
        or "clearance baixo" in m
        or "creatinina alta" in m
    ) and antibiotic in [
        "nitrofurantoina",
        "ciprofloxacino",
        "levofloxacino",
        "amoxicilina",
        "amoxicilina + clavulanato",
    ]:
        alerts.append(
            "Considerar avaliação da função renal para ajuste de dose ou adequação da escolha antibiótica."
        )

    if "gestante" in m or "gestacao" in m or "gravida" in m:
        alerts.append(
            "Confirmar a segurança do antibiótico no contexto gestacional e considerar a idade gestacional."
        )

    if (
        "amamentando" in m
        or "lactante" in m
        or "lactacao" in m
        or "lactação" in m
        or "aleitamento" in m
    ):
        alerts.append(
            "Confirmar a segurança do antibiótico durante lactação e orientar sobre sinais de efeitos adversos no lactente."
        )

    if ("hepatopatia" in m or "doenca hepatica" in m or "doença hepática" in m or "cirrose" in m):
        alerts.append(
            "Considerar comorbidade hepática na escolha antibiótica e avaliar necessidade de ajuste ou monitorização clínica."
        )

    return alerts
