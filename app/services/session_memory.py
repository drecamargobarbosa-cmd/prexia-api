from collections import defaultdict
from typing import Any, Dict, List


MAX_HISTORY = 12

conversation_memory: Dict[str, List[dict]] = defaultdict(list)
conversation_context: Dict[str, dict] = defaultdict(dict)


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
    conversation_context[user_id] = {}


def get_context(user_id: str) -> dict:
    context = conversation_context.get(user_id)

    if not context:
        context = {
            "scenario": None,
            "dados_clinicos": {
                "idade": None,
                "peso": None,
                "alergia": None,
                "gravidade": None,
            }
        }
        conversation_context[user_id] = context

    if "dados_clinicos" not in context:
        context["dados_clinicos"] = {
            "idade": None,
            "peso": None,
            "alergia": None,
            "gravidade": None,
        }

    if "scenario" not in context:
        context["scenario"] = None

    return context


def update_context(user_id: str, new_context: dict | None) -> dict:
    current = get_context(user_id)

    if not new_context:
        return current

    scenario = new_context.get("scenario")
    if scenario:
        current["scenario"] = scenario

    new_dados = new_context.get("dados_clinicos", {})
    current_dados = current.get("dados_clinicos", {})

    for key in ["idade", "peso", "alergia", "gravidade"]:
        if key in new_dados and new_dados[key] is not None:
            current_dados[key] = new_dados[key]

    current["dados_clinicos"] = current_dados
    conversation_context[user_id] = current

    return current


def set_context_value(user_id: str, key: str, value: Any) -> dict:
    current = get_context(user_id)
    current[key] = value
    conversation_context[user_id] = current
    return current


def reset_clinical_context(user_id: str) -> dict:
    current = get_context(user_id)
    current["scenario"] = None
    current["dados_clinicos"] = {
        "idade": None,
        "peso": None,
        "alergia": None,
        "gravidade": None,
    }
    conversation_context[user_id] = current
    return current
