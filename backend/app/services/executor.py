"""Tool execution layer.

execute_action is only ever called from approval_agent.execute_actions,
and only for items the human explicitly approved — see
backend/app/agents/approval_agent.py for the gate. Routes by action["type"]:
  - "email"    -> Gmail draft creation (users.drafts.create). DRAFT ONLY —
                  this code path must never call drafts.send or messages.send.
  - "calendar" -> Google Calendar events.insert.
  - "github"   -> GitHub issue creation, only for action items the action
                  agent classified as engineering work.
  - anything else ("task") -> tracked only; there is no external tool for
    generic action items, so this just records the decision.
"""
import base64
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText

import dateparser
import requests
from googleapiclient.discovery import build

from app.config import (
    CALENDAR_TIMEZONE, CALENDAR_DEFAULT_DURATION_MINUTES,
    GITHUB_TOKEN, GITHUB_REPO,
)
from app.services.google_auth import load_google_credentials, GoogleCredentialsNotConfigured

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# dateparser's strict grammar rejects "next"/"this" prefixes and vague
# day-part words ("Thursday morning"), so normalize before parsing.
_DAYPART_TIMES = {
    "morning": "09:00", "afternoon": "14:00", "evening": "18:00",
    "night": "20:00", "noon": "12:00", "midday": "12:00",
}
_FILLER_WORDS = re.compile(r"\b(next|this|the|upcoming|on|at)\b", re.IGNORECASE)


def _normalize_datetime_text(text: str) -> str:
    text = _FILLER_WORDS.sub("", text)
    for word, clock_time in _DAYPART_TIMES.items():
        text = re.sub(rf"\b{word}\b", clock_time, text, flags=re.IGNORECASE)
    return " ".join(text.split())


def execute_action(action: dict) -> dict:
    action_type = action.get("type", "task")

    if action_type == "email":
        return _create_gmail_draft(action)
    if action_type == "calendar":
        return _create_calendar_event(action)
    if action_type == "github":
        return _create_github_issue(action)
    return _track_task(action)


def _track_task(action: dict) -> dict:
    return {
        "status": "tracked",
        "action_id": action.get("id"),
        "message": f"Tracked (no external tool for plain tasks): {action.get('task')}",
    }


def _create_gmail_draft(action: dict) -> dict:
    """Create a Gmail draft via users.drafts.create. Never sends it."""
    try:
        creds = load_google_credentials()
    except GoogleCredentialsNotConfigured as e:
        return {
            "status": "failed",
            "action_id": action.get("id"),
            "message": f"Gmail not configured: {e}",
        }

    message = MIMEText(action.get("body", ""))
    message["to"] = ", ".join(action.get("recipients") or [])
    message["subject"] = action.get("subject", "")
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        service = build("gmail", "v1", credentials=creds)
        draft = service.users().drafts().create(
            userId="me", body={"message": {"raw": raw}}
        ).execute()
        return {
            "status": "drafted",
            "action_id": action.get("id"),
            "message": f"Gmail draft created (id={draft.get('id')}): {action.get('subject', '')}",
            "gmail_response": draft,
        }
    except Exception as e:
        return {
            "status": "failed",
            "action_id": action.get("id"),
            "message": f"Gmail draft creation failed: {e}",
        }


def _create_calendar_event(action: dict) -> dict:
    """Create a Google Calendar event via events.insert.

    The calendar agent produces free-text date/time (e.g. "Thursday
    morning") rather than ISO datetimes, so we resolve that here with
    dateparser, biased toward the next future occurrence.
    """
    try:
        creds = load_google_credentials()
    except GoogleCredentialsNotConfigured as e:
        return {
            "status": "failed",
            "action_id": action.get("id"),
            "message": f"Calendar not configured: {e}",
        }

    date_str = " ".join(filter(None, [action.get("date"), action.get("time")])).strip()
    start_dt = dateparser.parse(
        _normalize_datetime_text(date_str),
        settings={"RELATIVE_BASE": datetime.now(), "PREFER_DATES_FROM": "future"},
    ) if date_str else None

    if start_dt is None:
        return {
            "status": "failed",
            "action_id": action.get("id"),
            "message": f"Could not resolve a date/time from '{date_str}' for event '{action.get('title', '')}'.",
        }

    end_dt = start_dt + timedelta(minutes=CALENDAR_DEFAULT_DURATION_MINUTES)

    # attendees from the transcript are names ("Sarah", "marketing team"),
    # not email addresses — only pass through ones that look like real emails.
    attendees = [{"email": a} for a in (action.get("attendees") or []) if _EMAIL_RE.match(a)]

    event_body = {
        "summary": action.get("title", ""),
        "description": action.get("purpose", ""),
        "start": {"dateTime": start_dt.isoformat(), "timeZone": CALENDAR_TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": CALENDAR_TIMEZONE},
        "attendees": attendees,
    }

    try:
        service = build("calendar", "v3", credentials=creds)
        event = service.events().insert(calendarId="primary", body=event_body).execute()
        return {
            "status": "created",
            "action_id": action.get("id"),
            "message": f"Calendar event created (id={event.get('id')}): {event.get('htmlLink')}",
            "calendar_response": event,
        }
    except Exception as e:
        return {
            "status": "failed",
            "action_id": action.get("id"),
            "message": f"Calendar event creation failed: {e}",
        }


def _create_github_issue(action: dict) -> dict:
    """Create a GitHub issue via POST /repos/{owner}/{repo}/issues.

    Only called for action items the action agent classified as
    engineering work (is_engineering=True -> type="github").
    """
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return {
            "status": "failed",
            "action_id": action.get("id"),
            "message": "GitHub not configured: set GITHUB_TOKEN and GITHUB_REPO in .env.",
        }

    body_lines = [action.get("task", "")]
    if action.get("owner"):
        body_lines.append(f"\n**Owner:** {action['owner']}")
    if action.get("deadline"):
        body_lines.append(f"**Deadline:** {action['deadline']}")
    if action.get("priority"):
        body_lines.append(f"**Priority:** {action['priority']}")
    body_lines.append("\n_Created automatically from a MeetOps AI meeting action item._")

    try:
        resp = requests.post(
            f"https://api.github.com/repos/{GITHUB_REPO}/issues",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={
                "title": action.get("task", "")[:256],
                "body": "\n".join(body_lines),
                "labels": ["meetops-ai"],
            },
            timeout=15,
        )
        resp.raise_for_status()
        issue = resp.json()
        return {
            "status": "created",
            "action_id": action.get("id"),
            "message": f"GitHub issue #{issue.get('number')} created: {issue.get('html_url')}",
            "github_response": issue,
        }
    except Exception as e:
        return {
            "status": "failed",
            "action_id": action.get("id"),
            "message": f"GitHub issue creation failed: {e}",
        }
