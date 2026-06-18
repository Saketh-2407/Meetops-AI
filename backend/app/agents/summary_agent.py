from app.services.openai_client import structured_call
from app.schemas.meeting import MeetingSummary
from app.utils.prompts import SUMMARY_PROMPT


def summary_agent(state):
    result = structured_call(
        SUMMARY_PROMPT.format(transcript=state["transcript"]),
        MeetingSummary,
    )
    return {
        "meeting_title": result.meeting_title,
        "executive_summary": result.executive_summary,
        "key_points": result.key_points,
        "risks_or_blockers": result.risks_or_blockers,
    }
