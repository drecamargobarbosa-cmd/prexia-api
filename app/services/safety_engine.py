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


def assess_case_safety(
    scenario: str | None,
    dados_clinicos: dict | None,
    confidence: str | None = None,
) -> dict:
    dados = dados_clinicos or {}

    alertas_clinicos = []
    dados_relevantes_ausentes = []
    reavaliacao_necessaria = False
    nivel_seguranca = "adequado"

    if not scenario:
        return {
            "nivel_seguranca": "incerto",
            "reavaliacao_necessaria": True,
            "dados_relevantes_ausentes": ["cenario clinico"],
            "alertas_clinicos": [
                "Nao foi possivel definir o cenario clinico com seguranca."
            ]
        }

    if scenario == "otite_media_aguda":
        resultado = _assess_otitis_safety(dados)
        alertas_clinicos.extend(resultado["alertas_clinicos"])
        dados_relevantes_ausentes.extend(resultado["dados_relevantes_ausentes"])
        reavaliacao_necessaria = resultado["reavaliacao_necessaria"]
        nivel_seguranca = resultado["nivel_seguranca"]

    elif scenario == "faringoamigdalite":
        resultado = _assess_pharyngotonsillitis_safety(dados)
        alertas_clinicos.extend(resultado["alertas_clinicos"])
        dados_relevantes_ausentes.extend(resultado["dados_relevantes_ausentes"])
        reavaliacao_necessaria = resultado["reavaliacao_necessaria"]
        nivel_seguranca = resultado["nivel_seguranca"]

    elif scenario == "sinusite":
        resultado = _assess_sinusitis_safety(dados)
        alertas_clinicos.extend(resultado["alertas_clinicos"])
        dados_relevantes_ausentes.extend(resultado["dados_relevantes_ausentes"])
        reavaliacao_necessaria = resultado["reavaliacao_necessaria"]
        nivel_seguranca = resultado["nivel_seguranca"]

    else:
        nivel_seguranca = "incerto"
        reavaliacao_necessaria = True
        alertas_clinicos.append(
            "Cenario ainda sem regras de seguranca especificas implementadas."
        )

    if confidence == "baixa":
        if "A confianca da recomendacao esta baixa; validar clinicamente antes de prescrever." not in alertas_clinicos:
            alertas_clinicos.append(
                "A confianca da recomendacao esta baixa; validar clinicamente antes de prescrever."
            )
        reavaliacao_necessaria = True
        if nivel_seguranca == "adequado":
            nivel_seguranca = "atencao"

    elif confidence == "moderada" and nivel_seguranca == "adequado":
        nivel_seguranca = "atencao"

    return {
        "nivel_seguranca": nivel_seguranca,
        "reavaliacao_necessaria": reavaliacao_necessaria,
        "dados_relevantes_ausentes": _unique_list(dados_relevantes_ausentes),
        "alertas_clinicos": _unique_list(alertas_clinicos)
    }


def _assess_otitis_safety(dados: dict) -> dict:
    alertas = []
    ausentes = []
    reavaliacao = False
    nivel = "adequado"

    idade = dados.get("idade")
    peso = dados.get("peso")
    dor_intensa = dados.get("dor_intensa")
    toxemia = dados.get("toxemia")
    prostracao = dados.get("prostracao")
    secrecao = dados.get("secrecao_auricular")
    alergia = dados.get("alergia")

    if idade is None:
        ausentes.append("idade")
        nivel = "atencao"

    if idade is not None and idade < 12 and peso is None:
        ausentes.append("peso")
        alertas.append("Em pediatria, o peso e necessario para validar dose com seguranca.")
        reavaliacao = True
        nivel = "atencao"

    if dor_intensa is None:
        ausentes.append("intensidade da dor")
    if toxemia is None:
        ausentes.append("toxemia")
    if prostracao is None:
        ausentes.append("prostracao")

    if dor_intensa is True:
        alertas.append("Dor intensa pode indicar maior gravidade e necessidade de reavaliacao clinica mais proxima.")
        nivel = "atencao"

    if toxemia is True or prostracao is True:
        alertas.append("Presenca de toxemia ou prostracao eleva risco clinico e exige avaliacao mais cautelosa.")
        reavaliacao = True
        nivel = "critico"

    if secrecao is True:
        alertas.append("Secrecao auricular sugere maior relevancia clinica do quadro e necessidade de seguimento.")
        if nivel == "adequado":
            nivel = "atencao"

    if alergia is None:
        ausentes.append("status de alergia a penicilina")

    return {
        "nivel_seguranca": nivel,
        "reavaliacao_necessaria": reavaliacao,
        "dados_relevantes_ausentes": ausentes,
        "alertas_clinicos": alertas
    }


def _assess_pharyngotonsillitis_safety(dados: dict) -> dict:
    alertas = []
    ausentes = []
    reavaliacao = False
    nivel = "adequado"

    idade = dados.get("idade")
    peso = dados.get("peso")
    toxemia = dados.get("toxemia")
    prostracao = dados.get("prostracao")
    alergia = dados.get("alergia")

    if idade is None:
        ausentes.append("idade")
        nivel = "atencao"

    if idade is not None and idade < 12 and peso is None:
        ausentes.append("peso")
        alertas.append("Em pediatria, o peso e necessario para validar dose com seguranca.")
        reavaliacao = True
        nivel = "atencao"

    if toxemia is None:
        ausentes.append("toxemia")
    if prostracao is None:
        ausentes.append("prostracao")

    if toxemia is True or prostracao is True:
        alertas.append("Toxemia ou prostracao sugerem necessidade de avaliacao presencial mais cautelosa.")
        reavaliacao = True
        nivel = "critico"

    if alergia is None:
        ausentes.append("status de alergia a penicilina")

    return {
        "nivel_seguranca": nivel,
        "reavaliacao_necessaria": reavaliacao,
        "dados_relevantes_ausentes": ausentes,
        "alertas_clinicos": alertas
    }


def _assess_sinusitis_safety(dados: dict) -> dict:
    alertas = []
    ausentes = []
    reavaliacao = False
    nivel = "adequado"

    idade = dados.get("idade")
    peso = dados.get("peso")
    duracao = dados.get("duracao_dias")
    febre = dados.get("febre")
    toxemia = dados.get("toxemia")
    prostracao = dados.get("prostracao")
    alergia = dados.get("alergia")

    if idade is None:
        ausentes.append("idade")
        nivel = "atencao"

    if idade is not None and idade < 12 and peso is None:
        ausentes.append("peso")
        alertas.append("Em pediatria, o peso e necessario para validar dose com seguranca.")
        reavaliacao = True
        nivel = "atencao"

    if duracao is None:
        ausentes.append("tempo de evolucao")

    if febre is None:
        ausentes.append("febre")

    if toxemia is None:
        ausentes.append("toxemia")

    if prostracao is None:
        ausentes.append("prostracao")

    if toxemia is True or prostracao is True:
        alertas.append("Toxemia ou prostracao podem indicar maior gravidade e exigem avaliacao presencial mais cautelosa.")
        reavaliacao = True
        nivel = "critico"

    if duracao is not None and duracao < 10:
        alertas.append("Tempo de evolucao inferior a 10 dias reduz a probabilidade de sinusite bacteriana.")
        if nivel == "adequado":
            nivel = "atencao"

    if alergia is None:
        ausentes.append("status de alergia a penicilina")

    return {
        "nivel_seguranca": nivel,
        "reavaliacao_necessaria": reavaliacao,
        "dados_relevantes_ausentes": ausentes,
        "alertas_clinicos": alertas
    }


def _unique_list(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
