from app.services.llm_service import LLMService


def main():
    print("Iniciando teste LLM...")

    llm = LLMService()

    print("Enviando requisição para OpenAI...")

    resposta = llm.generate("Responda exatamente: OK")

    print("Resposta recebida:")
    print(resposta)


if __name__ == "__main__":
    main()
