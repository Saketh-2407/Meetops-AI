from app.services.openai_client import structured_call
from app.schemas.meeting import CalendarSuggestionList
from app.utils.prompts import CALENDAR_PROMPT


def calendar_agent(state):
    result = structured_call(
        CALENDAR_PROMPT.format(
            transcript=state["transcript"],
            action_items=state.get("action_items", []),
        ),
        CalendarSuggestionList,
    )
    return {
        "calendar_suggestions": [c.model_dump() for c in result.calendar_suggestions]
    }
