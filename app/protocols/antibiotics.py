ANTIBIOTIC_PROTOCOLS = {
    "sinusite_bacteriana": {
        "keywords": [
            "sinusite",
            "sinusite bacteriana",
            "rinossinusite",
            "rinossinusite bacteriana",
            "dor facial",
            "secrecao purulenta",
            "secreção purulenta",
            "congestao nasal",
            "congestão nasal"
        ],
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
            "Considerar perfil local de resistência"
        ]
    },
    "itu_nao_complicada": {
        "keywords": [
            "itu",
            "infeccao urinaria",
            "infecção urinária",
            "cistite",
            "disuria",
            "disúria",
            "ardor ao urinar",
            "dor ao urinar",
            "queimacao ao urinar",
            "queimação ao urinar",
            "urgencia urinaria",
            "urgência urinária",
            "polaciuria",
            "polaciúria"
        ],
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
        "keywords": [
            "odontogenica",
            "odontogênica",
            "odonto",
            "dente",
            "dor de dente",
            "abscesso dentario",
            "abscesso dentário",
            "infeccao dentaria",
            "infecção dentária",
            "infeccao odontologica",
            "infecção odontológica",
            "celulite odontogenica",
            "celulite odontogênica"
        ],
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
            "Antibiótico não substitui abordagem odontológica local",
            "Avaliar drenagem, foco infeccioso e sinais sistêmicos",
            "Escalonar se houver celulite extensa ou sinais de gravidade"
        ]
    },
    "otite_media_aguda": {
        "keywords": [
            "otite",
            "otite media aguda",
            "otite média aguda",
            "otite media",
            "otite média",
            "dor de ouvido",
            "ouvido",
            "otalgia",
            "ouvido inflamado"
        ],
        "primeira_linha": {
            "medicamento": "amoxicilina",
            "dose": "50 a 90 mg/kg/dia divididos em 2 ou 3 doses",
            "duracao": "5 a 10 dias"
        },
        "alergia_penicilina": {
            "medicamento": "azitromicina",
            "dose": "10 mg/kg no primeiro dia, depois 5 mg/kg/dia",
            "duracao": "5 dias"
        },
        "observacoes": [
            "Confirmar critérios clínicos de otite média aguda",
            "Nem todos os casos exigem antibiótico imediato",
            "Avaliar idade e gravidade antes de iniciar antibiótico"
        ],
        "perguntas_obrigatorias": [
            "Qual a idade do paciente?",
            "Há sinais de gravidade, como febre alta, dor intensa ou toxemia?",
            "O paciente tem alergia à penicilina?"
        ]
    }
}
