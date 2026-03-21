from copy import deepcopy


class MemoryService:
    """
    Serviço responsável por armazenar e recuperar contexto por user_id.

    Atualmente usa memória em RAM.
    No futuro pode ser substituído por Redis ou banco de dados.
    """

    MEMORY = {}

    def get(self, user_id: str) -> dict:
        return deepcopy(self.MEMORY.get(user_id, {}))

    def save(self, user_id: str, context: dict):
        self.MEMORY[user_id] = deepcopy(context)

    def clear(self, user_id: str):
        if user_id in self.MEMORY:
            del self.MEMORY[user_id]
