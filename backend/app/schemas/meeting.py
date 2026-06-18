from typing import List, Optional, Literal

from pydantic import BaseModel, Field


# --- Summary -----------------------------------------------------------------
class MeetingSummary(BaseModel):
    meeting_title: str
    executive_summary: str
    key_points: List[str]
    risks_or_blockers: List[str]


# --- Decisions ---------------------------------------------------------------
class Decision(BaseModel):
    decision: str
    reason: Optional[str] = None
    confidence: float = Field(description="Confidence between 0 and 1")


class DecisionList(BaseModel):
    decisions: List[Decision]


# --- Action items ------------------------------------------------------------
# The model fills the draft; status/id are stamped in code afterwards.
class ActionItemDraft(BaseModel):
    task: str
    owner: Optional[str] = None
    deadline: Optional[str] = None
    priority: Literal["low", "medium", "high", "urgent"]
    is_engineering: bool = Field(
        default=False,
        description="True if this is a software engineering task (bug fix, code "
        "change, infra/deploy work) that belongs in an issue tracker rather than "
        "a generic follow-up.",
    )


class ActionItemList(BaseModel):
    action_items: List[ActionItemDraft]


# --- Calendar ----------------------------------------------------------------
class CalendarSuggestion(BaseModel):
    title: str
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: List[str] = []
    purpose: str


class CalendarSuggestionList(BaseModel):
    calendar_suggestions: List[CalendarSuggestion]


# --- Email -------------------------------------------------------------------
class EmailDraft(BaseModel):
    subject: str
    body: str
    recipients: List[str] = []
