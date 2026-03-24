import os
import json
from typing import Dict, Any
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class LLMExtractor:

    def extract(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai dados clínicos estruturados via LLM.
        Não toma decisão clínica, apenas estrutura os dados da mensagem.
        """

        prompt = self._build_prompt(message, context)

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é um extrator clínico estruturado. "
                            "Responda apenas em JSON válido, sem texto adicional, "
                            "sem blocos de código, sem explicações."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            content = response.choices[0].message.content

            if not content:
                return {}

            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            return json.loads(content)

        except json.JSONDecodeError:
            return {}
        except Exception as e:
            print(f"[LLMExtractor] Erro na extração: {e}")
            return {}

    def _build_prompt(self, message: str, context: Dict[str, Any]) -> str:

        return f"""Analise a mensagem clínica abaixo e extraia os dados estruturados.

Mensagem:
{message}

Contexto anterior (já conhecido):
{json.dumps(context, ensure_ascii=False, indent=2)}

Retorne apenas um JSON válido no formato abaixo. Use null para campos não mencionados.
Não repita valores que já estão no contexto anterior a menos que a mensagem os confirme ou corrija.

{{
  "idade": null,
  "peso": null,
  "sexo": null,

  "scenario": null,

  "symptoms": {{
    "dor_presente": null,
    "dor_intensa": null,
    "febre": null,
    "febre_alta": null,
    "toxemia": null,
    "prostracao": null,
    "duracao_dias": null,
    "secrecao_auricular": null,
    "secrecao_purulenta": null,
    "dor_garganta": null,
    "placas_amigdalianas": null,
    "dor_facial": null,
    "secrecao_nasal_purulenta": null
  }},

  "risk_factors": {{
    "alergia_penicilina": null,
    "gestante": null,
    "lactante": null,
    "doenca_renal": null,
    "hepatopatia": null
  }}
}}

Valores aceitos:
- idade: número inteiro ou null
- peso: número decimal ou null
- sexo: "masculino", "feminino" ou null
- scenario: "otite_media_aguda", "faringoamigdalite", "sinusite" ou null
- todos os campos de symptoms e risk_factors: true, false ou null
- duracao_dias: número inteiro ou null
"""
