from collections import defaultdict
from typing import Dict, List


MAX_HISTORY = 12

conversation_memory: Dict[str, List[dict]] = defaultdict(list)


def add_message(user_id: str, role: str, content: str) -> None:
    conversation_memory[user_id].append({
        "role": role,
        "content": content
    })

    if len(conversation_memory[user_id]) > MAX_HISTORY:
        conversation_memory[user_id] = conversation_memory[user_id][-MAX_HISTORY:]


def get_history(user_id: str) -> List[dict]:
    return conversation_memory[user_id]


def clear_history(user_id: str) -> None:
    conversation_memory[user_id] = []
