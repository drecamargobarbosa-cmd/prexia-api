from app.services.llm_service import LLMService


def main():
    llm = LLMService()
    resposta = llm.generate("Responda apenas: conexão com OpenAI funcionando")
    print(resposta)


if __name__ == "__main__":
    main()
