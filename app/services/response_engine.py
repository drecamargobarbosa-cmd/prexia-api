class ResponseEngine:

    def build_response(self, protocol: dict | None, scenario: str | None):

        if not protocol:
            return {
                "tipo": "fallback",
                "cenario": scenario,
                "resposta": "Ainda não há protocolo estruturado para este cenário.",
                "antibiotico_sugerido": None,
                "dose": None,
                "duracao": None,
                "alternativas": [],
                "alertas_protocolo": [],
                "interacoes_medicamentosas": [],
                "red_flags": [],
                "confirmacao_necessaria": True,
                "perguntas_obrigatorias": [
                    "Pode detalhar melhor o quadro clínico?",
                    "Qual a idade do paciente?",
                    "Há alergias medicamentosas?"
                ],
                "fonte": "fallback_clinico_v1"
            }

        primeira_linha = protocol.get("primeira_linha", {})
        alternativas = protocol.get("alternativas", [])
        perguntas_obrigatorias = protocol.get("perguntas_obrigatorias", [])
        alertas = protocol.get("alertas", [])
        red_flags = protocol.get("red_flags", [])

        return {
            "tipo": "protocolo",
            "cenario": protocol.get("titulo", scenario),
            "resposta": protocol.get(
                "resposta_base",
                "Protocolo identificado com sucesso."
            ),
            "antibiotico_sugerido": primeira_linha.get("antibiotico"),
            "dose": primeira_linha.get("dose"),
            "duracao": primeira_linha.get("duracao"),
            "alternativas": alternativas,
            "alertas_protocolo": alertas,
            "interacoes_medicamentosas": [],
            "red_flags": red_flags,
            "confirmacao_necessaria": len(perguntas_obrigatorias) > 0,
            "perguntas_obrigatorias": perguntas_obrigatorias,
            "fonte": protocol.get("fonte", "protocolo_local_v1")
        }
