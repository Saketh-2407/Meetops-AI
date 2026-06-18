from app.services.openai_client import structured_call
from app.schemas.meeting import EmailDraft
from app.utils.prompts import EMAIL_PROMPT


def email_agent(state):
    result = structured_call(
        EMAIL_PROMPT.format(
            transcript=state["transcript"],
            decisions=state.get("decisions", []),
            action_items=state.get("action_items", []),
        ),
        EmailDraft,
    )
    return {"follow_up_email": result.model_dump()}
