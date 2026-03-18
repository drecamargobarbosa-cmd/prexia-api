class ResponseEngine:

    def build_response(self, protocol, scenario):
        if not protocol:
            return {
                "tipo": "sem_protocolo",
                "cenario": scenario,
                "resposta": "Nao tenho protocolo para esse cenario no momento.",
                "antibiotico_sugerido": None,
                "dose": None,
                "duracao": None,
                "alternativas": [],
                "alertas_protocolo": [],
                "interacoes_medicamentosas": [],
                "red_flags": [],
                "confirmacao_necessaria": False,
                "perguntas_obrigatorias": [],
                "fonte": "protocolo_local_v1"
            }

        primeira_linha = protocol.get("primeira_linha", {})
        alternativa = protocol.get("alternativa", {})
        alergia_penicilina = protocol.get("alergia_penicilina", {})

        alternativas = []

        if alternativa.get("medicamento"):
            alternativas.append(alternativa.get("medicamento"))

        if alergia_penicilina.get("medicamento"):
            alternativas.append(alergia_penicilina.get("medicamento"))

        return {
            "tipo": "protocolo",
            "cenario": scenario,
            "resposta": "TESTE",
            "antibiotico_sugerido": "amoxicilina_teste",
            "dose": "dose_teste",
            "duracao": "duracao_teste",
            "alternativas": alternativas,
            "alertas_protocolo": protocol.get("observacoes", []),
            "interacoes_medicamentosas": [],
            "red_flags": [],
            "confirmacao_necessaria": False,
            "perguntas_obrigatorias": [],
            "fonte": "protocolo_local_v1"
        }
