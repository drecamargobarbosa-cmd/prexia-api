ANTIBIOTIC_PROTOCOLS = {

    "otite_media_aguda": {

        "sinonimos": [
            "otite",
            "otite media",
            "otite media aguda",
            "dor de ouvido",
            "otalgia",
            "ouvido inflamado"
        ],

        "sintomas_chave": [
            "dor de ouvido",
            "otalgia",
            "febre",
            "irritabilidade",
            "secrecao auricular"
        ],

        "criterios_gravidade": [
            "febre alta",
            "dor intensa",
            "toxemia"
        ],

        "perguntas_obrigatorias": [
            "Há sinais de gravidade, como febre alta, dor intensa ou toxemia?",
            "O paciente tem alergia à penicilina?"
        ],

        "tratamento": {

            "primeira_linha": {
                "medicamento": "Amoxicilina",
                "apresentacao": "500 mg cápsulas",
                "posologia": "Tomar 1 cápsula por via oral a cada 8 horas",
                "duracao": "7 dias",
                "quantidade_total": "21 cápsulas",
                "justificativa": "Primeira escolha para otite média aguda por cobertura adequada dos principais agentes etiológicos."
            },

            "alergia_penicilina": {
                "medicamento": "Azitromicina",
                "apresentacao": "500 mg comprimidos",
                "posologia": "Tomar 1 comprimido por via oral 1 vez ao dia",
                "duracao": "3 dias",
                "quantidade_total": "3 comprimidos",
                "justificativa": "Alternativa em pacientes com alergia à penicilina."
            }

        }
    },

    "amigdalite_bacteriana": {

        "sinonimos": [
            "amigdalite",
            "dor de garganta",
            "odinofagia",
            "faringite",
            "placa na garganta",
            "exsudato amigdaliano"
        ],

        "sintomas_chave": [
            "dor de garganta",
            "odinofagia",
            "febre",
            "placas",
            "aumento de amigdala"
        ],

        "criterios_gravidade": [
            "febre alta",
            "dificuldade para deglutir",
            "toxemia"
        ],

        "perguntas_obrigatorias": [
            "Há presença de febre?",
            "Há placas ou exsudato nas amígdalas?",
            "O paciente tem alergia à penicilina?"
        ],

        "tratamento": {

            "primeira_linha": {
                "medicamento": "Amoxicilina",
                "apresentacao": "500 mg cápsulas",
                "posologia": "Tomar 1 cápsula por via oral a cada 8 horas",
                "duracao": "10 dias",
                "quantidade_total": "30 cápsulas",
                "justificativa": "Tratamento padrão para amigdalite bacteriana por Streptococcus pyogenes."
            },

            "alergia_penicilina": {
                "medicamento": "Azitromicina",
                "apresentacao": "500 mg comprimidos",
                "posologia": "Tomar 1 comprimido por via oral 1 vez ao dia",
                "duracao": "5 dias",
                "quantidade_total": "5 comprimidos",
                "justificativa": "Alternativa em pacientes alérgicos à penicilina."
            }

        }
    }
}
