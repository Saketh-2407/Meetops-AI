from langgraph.types import interrupt

from app.services.executor import execute_action


def _build_pending_items(state):
    """Collect every approvable item — tasks, the follow-up email, and each
    calendar suggestion — into one list with a synthetic id + type so the
    same approval_decisions dict can gate all of them."""
    items = []

    for action in state.get("action_items", []):
        if action.get("status") == "pending_approval":
            items.append(action)

    email = state.get("follow_up_email")
    if email and email.get("status", "pending_approval") == "pending_approval":
        items.append({
            "id": "email_1",
            "type": "email",
            "task": f"Send follow-up email: {email.get('subject', '')}",
            "status": "pending_approval",
            **email,
        })

    for i, suggestion in enumerate(state.get("calendar_suggestions", [])):
        if suggestion.get("status", "pending_approval") == "pending_approval":
            items.append({
                "id": f"calendar_{i + 1}",
                "type": "calendar",
                "task": f"Create calendar event: {suggestion.get('title', '')}",
                "status": "pending_approval",
                **suggestion,
            })

    return items


def human_approval(state):
    """Pause the graph and surface every pending action — tasks, the email
    draft, and calendar suggestions — for human review.

    interrupt() saves state via the checkpointer and returns control to the
    caller (FastAPI). The graph resumes when invoked again with
    Command(resume=<decisions>), where decisions is {item_id: "approved"|"rejected"}.
    """
    pending = _build_pending_items(state)

    decisions = interrupt(
        {
            "type": "approval_request",
            "pending_actions": pending,
        }
    )

    return {"approval_decisions": decisions or {}}


def execute_actions(state):
    """Execute only approved items (tasks, email draft, calendar suggestions)
    and write an audit log entry for each. Nothing here runs unless the
    corresponding id was explicitly approved in approval_decisions."""
    decisions = state.get("approval_decisions", {})

    executed = []
    audit = list(state.get("audit_log", []))

    # --- task action items ---------------------------------------------
    updated_actions = []
    for action in state.get("action_items", []):
        aid = action.get("id")
        decision = decisions.get(aid, "rejected")
        if decision == "approved":
            result = execute_action({**action, "type": action.get("type", "task")})
            updated_actions.append({**action, "status": result["status"]})
            executed.append(result)
            audit.append({"action_id": aid, "status": result["status"], "details": result["message"]})
        else:
            updated_actions.append({**action, "status": "rejected"})
            audit.append({"action_id": aid, "status": "rejected", "details": "Rejected by user"})

    # --- follow-up email --------------------------------------------------
    updated_email = state.get("follow_up_email")
    if updated_email:
        decision = decisions.get("email_1", "rejected")
        if decision == "approved":
            result = execute_action({"id": "email_1", "type": "email", **updated_email})
            updated_email = {**updated_email, "status": result["status"]}
            executed.append(result)
            audit.append({"action_id": "email_1", "status": result["status"], "details": result["message"]})
        else:
            updated_email = {**updated_email, "status": "rejected"}
            audit.append({"action_id": "email_1", "status": "rejected", "details": "Rejected by user"})

    # --- calendar suggestions ----------------------------------------------
    updated_calendar = []
    for i, suggestion in enumerate(state.get("calendar_suggestions", [])):
        cid = f"calendar_{i + 1}"
        decision = decisions.get(cid, "rejected")
        if decision == "approved":
            result = execute_action({"id": cid, "type": "calendar", **suggestion})
            updated_calendar.append({**suggestion, "status": result["status"]})
            executed.append(result)
            audit.append({"action_id": cid, "status": result["status"], "details": result["message"]})
        else:
            updated_calendar.append({**suggestion, "status": "rejected"})
            audit.append({"action_id": cid, "status": "rejected", "details": "Rejected by user"})

    return {
        "action_items": updated_actions,
        "follow_up_email": updated_email,
        "calendar_suggestions": updated_calendar,
        "executed_actions": executed,
        "audit_log": audit,
    }
