class ReasoningEngine:
    """
    Responsável por raciocínio clínico.

    Não aplica protocolo.
    Não define medicamento.

    Apenas decide:
    - já posso tratar?
    - preciso de mais dados?
    - é seguro avançar?
    """

    def evaluate_readiness(self, contexto: dict) -> dict:
        dados = contexto.get("dados_clinicos", {})
        scenario = contexto.get("scenario")

        if not scenario:
            return {
                "status": "insufficient_data",
                "reason": "Sem cenário clínico definido"
            }

        # Exemplo para otite (expandiremos depois)
        if scenario == "otite_media_aguda":
            if dados.get("dor_presente") and dados.get("duracao_dias"):
                if (
                    dados.get("febre") or
                    dados.get("secrecao_auricular") or
                    dados.get("dor_intensa")
                ):
                    return {
                        "status": "ready_for_treatment"
                    }

            return {
                "status": "need_more_data",
                "missing": self._missing_otitis_data(dados)
            }

        return {
            "status": "unknown_scenario"
        }

    def _missing_otitis_data(self, dados):
        missing = []

        if dados.get("febre") is None:
            missing.append("Há febre?")
        if dados.get("duracao_dias") is None:
            missing.append("Há quantos dias?")
        if dados.get("secrecao_auricular") is None:
            missing.append("Há secreção?")

        return missing
