from app.services.openai_client import structured_call
from app.schemas.meeting import DecisionList
from app.utils.prompts import DECISION_PROMPT


def decision_agent(state):
    result = structured_call(
        DECISION_PROMPT.format(transcript=state["transcript"]),
        DecisionList,
    )
    return {"decisions": [d.model_dump() for d in result.decisions]}
