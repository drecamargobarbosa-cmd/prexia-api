import json
from typing import Dict, Any
from openai import OpenAI

client = OpenAI()


class LLMExtractor:

    def extract(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai dados clínicos estruturados via LLM.
        NÃO toma decisão clínica.
        """

        prompt = self._build_prompt(message, context)

        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "Você é um extrator clínico estruturado. Responda apenas em JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        content = response.choices[0].message.content

        try:
            return json.loads(content)
        except Exception:
            return {}

    def _build_prompt(self, message: str, context: Dict[str, Any]) -> str:

        return f"""
Analise a mensagem clínica abaixo e extraia os dados estruturados.

Mensagem:
{message}

Contexto anterior:
{json.dumps(context, ensure_ascii=False)}

Retorne apenas JSON no formato:

{{
  "idade": int ou null,
  "peso": float ou null,
  "sexo": "masculino/feminino/null",

  "scenario": "otite_media_aguda/faringite/sinusite/geral",

  "symptoms": {{
    "dor_presente": true/false/null,
    "dor_intensa": true/false/null,
    "febre": true/false/null,
    "febre_alta": true/false/null,
    "toxemia": true/false/null,
    "prostracao": true/false/null,
    "duracao_dias": int ou null,

    "secrecao_auricular": true/false/null,
    "secrecao_purulenta": true/false/null,
    "dor_garganta": true/false/null,
    "placas_amigdalianas": true/false/null,
    "dor_facial": true/false/null,
    "secrecao_nasal_purulenta": true/false/null
  }},

  "risk_factors": {{
    "alergia_penicilina": true/false/null,
    "gestante": true/false/null,
    "lactante": true/false/null,
    "doenca_renal": true/false/null,
    "hepatopatia": true/false/null
  }}
}}
"""
