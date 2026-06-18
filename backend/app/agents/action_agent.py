from app.services.openai_client import structured_call
from app.schemas.meeting import ActionItemList
from app.utils.prompts import ACTION_PROMPT


def action_agent(state):
    result = structured_call(
        ACTION_PROMPT.format(transcript=state["transcript"]),
        ActionItemList,
    )
    action_items = []
    for i, item in enumerate(result.action_items):
        data = item.model_dump()
        data["id"] = f"action_{i + 1}"
        data["type"] = "github" if data.pop("is_engineering", False) else "task"
        data["status"] = "pending_approval"
        action_items.append(data)
    return {"action_items": action_items}
