from app.services.safety_engine import normalize


class ResponseEngine:

    def build_alternatives(
        self,
        protocol: dict,
        medicamento_escolhido: str | None = None,
    ) -> list[str]:
        alternativas = []

        alternativa = protocol.get("alternativa", {})
        alergia_penicilina = protocol.get("alergia_penicilina", {})

        for opcao in [alternativa, alergia_penicilina]:
            medicamento = opcao.get("medicamento")
            if not medicamento:
                continue

            if medicamento_escolhido and normalize(medicamento) == normalize(medicamento_escolhido):
                continue

            if medicamento not in alternativas:
                alternativas.append(medicamento)

        return alternativas

    def build_response(
        self,
        protocol: dict | None,
        scenario: str | None,
        usar_alergia: bool = False,
    ) -> dict:
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
        alergia_penicilina = protocol.get("alergia_penicilina", {})

        if usar_alergia and alergia_penicilina:
            medicamento_escolhido = alergia_penicilina.get("medicamento")
            dose_escolhida = alergia_penicilina.get("dose")
            duracao_escolhida = alergia_penicilina.get("duracao")
            justificativa = "Paciente com alergia à penicilina."
        else:
            medicamento_escolhido = primeira_linha.get("medicamento")
            dose_escolhida = primeira_linha.get("dose")
            duracao_escolhida = primeira_linha.get("duracao")
            justificativa = "Primeira linha conforme protocolo."

        alternativas = self.build_alternatives(
            protocol=protocol,
            medicamento_escolhido=medicamento_escolhido,
        )

        return {
            "tipo": "protocolo",
            "cenario": scenario,
            "resposta": f"Protocolo identificado com sucesso. {justificativa}",
            "antibiotico_sugerido": medicamento_escolhido,
            "dose": dose_escolhida,
            "duracao": duracao_escolhida,
            "alternativas": alternativas,
            "alertas_protocolo": protocol.get("observacoes", []),
            "interacoes_medicamentosas": [],
            "red_flags": [],
            "confirmacao_necessaria": False,
            "perguntas_obrigatorias": protocol.get("perguntas_obrigatorias", []),
            "fonte": "protocolo_local_v1"
        }
