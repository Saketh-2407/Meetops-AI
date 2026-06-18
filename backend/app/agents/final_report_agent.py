from app.services.openai_client import client
from app.config import MODEL_NAME
from app.utils.prompts import FINAL_REPORT_PROMPT


def final_report_agent(state):
    prompt = FINAL_REPORT_PROMPT.format(
        executive_summary=state.get("executive_summary"),
        key_points=state.get("key_points"),
        decisions=state.get("decisions"),
        action_items=state.get("action_items"),
        risks=state.get("risks_or_blockers"),
        calendar=state.get("calendar_suggestions"),
        email=state.get("follow_up_email"),
    )
    response = client.responses.create(model=MODEL_NAME, input=prompt)
    return {"final_report": response.output_text}
