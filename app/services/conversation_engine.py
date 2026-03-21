from app.services.clinical_engine import ClinicalEngine
from app.services.memory_service import MemoryService


class ConversationEngine:
    """
    Responsável por orquestrar a interação com o usuário.

    - Recupera contexto
    - Chama o motor clínico
    - Salva o contexto atualizado
    """

    def __init__(self):
        self.clinical_engine = ClinicalEngine()
        self.memory_service = MemoryService()

    def process(self, message: str, user_id: str):
        # 1. Recuperar contexto salvo
        contexto = self.memory_service.get(user_id)

        # 2. Processar no motor clínico
        result = self.clinical_engine.evaluate(
            question=message,
            contexto=contexto,
            user_id=user_id
        )

        # 3. Salvar contexto atualizado
        updated_context = result.get("context", {})
        self.memory_service.save(user_id, updated_context)

        return result
