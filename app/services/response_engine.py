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
