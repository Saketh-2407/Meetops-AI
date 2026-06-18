from typing import TypedDict, List, Optional, Dict, Any


class MeetingState(TypedDict, total=False):
    transcript: str
    meeting_title: Optional[str]
    executive_summary: Optional[str]
    key_points: List[str]
    decisions: List[Dict[str, Any]]
    action_items: List[Dict[str, Any]]
    risks_or_blockers: List[str]
    calendar_suggestions: List[Dict[str, Any]]
    follow_up_email: Optional[Dict[str, Any]]
    # Human-in-the-loop
    approval_decisions: Dict[str, str]      # action_id -> "approved" | "rejected"
    executed_actions: List[Dict[str, Any]]
    audit_log: List[Dict[str, Any]]
    final_report: Optional[str]
