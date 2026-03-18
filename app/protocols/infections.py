INFECTION_PROTOCOLS = {
    "sinusite_bacteriana": {
        "keywords": ["sinusite"],
        "primeira_linha": {
            "medicamento": "amoxicilina + clavulanato",
            "dose": "875/125 mg a cada 12 horas",
            "duracao": "5 a 7 dias"
        },
        "alergia_penicilina": {
            "medicamento": "azitromicina",
            "dose": "500 mg 1x ao dia",
            "duracao": "3 dias"
        },
        "observacoes": [
            "Confirmar critérios clínicos de sinusite bacteriana",
            "Reavaliar se não houver melhora clínica",
            "Considerar perfil local de resistência bacteriana"
        ]
    },
    "itu_nao_complicada": {
        "keywords": ["itu", "infecção urinária", "infeccao urinaria", "cistite"],
        "primeira_linha": {
            "medicamento": "nitrofurantoína",
            "dose": "100 mg a cada 6 horas",
            "duracao": "5 dias"
        },
        "alternativa": {
            "medicamento": "fosfomicina",
            "dose": "3 g dose única",
            "duracao": "dose única"
        },
        "observacoes": [
            "Confirmar ausência de sinais de pielonefrite",
            "Avaliar gestação",
            "Avaliar função renal"
        ]
    },
    "infeccao_odontogenica": {
        "keywords": ["odontogênica", "odontogenica", "dente", "dentária", "dentaria", "abscesso dentário", "abscesso dentario"],
        "primeira_linha": {
            "medicamento": "amoxicilina",
            "dose": "500 mg a cada 8 horas",
            "duracao": "5 a 7 dias"
        },
        "alergia_penicilina": {
            "medicamento": "clindamicina",
            "dose": "300 mg a cada 6 horas",
            "duracao": "5 a 7 dias"
        },
        "observacoes": [
            "Antibiótico não substitui drenagem e abordagem odontológica local",
            "Avaliar foco infeccioso e sinais sistêmicos",
            "Escalonar se houver celulite extensa ou sinais de gravidade"
        ]
    }
}
