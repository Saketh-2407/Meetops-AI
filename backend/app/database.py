from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import models so they register on Base before create_all.
    from app.models import meeting  # noqa: F401
    Base.metadata.create_all(bind=engine)


def persist_meeting_results(transcript: str, state: dict) -> int:
    """Write one meeting row + all child rows after /resume completes.

    Called only once the full final state is available — decisions, action
    items with resolved statuses, email draft, calendar suggestions, and the
    audit log.  Returns the new meeting.id.
    """
    from app.models.meeting import (
        Meeting, DecisionRow, ActionItemRow,
        EmailDraftRow, CalendarSuggestionRow, AuditLogRow,
    )

    db = SessionLocal()
    try:
        meeting = Meeting(
            title=state.get("meeting_title"),
            transcript=transcript,
            summary=state.get("executive_summary"),
        )
        db.add(meeting)
        db.flush()  # assign meeting.id before inserting children

        for d in (state.get("decisions") or []):
            db.add(DecisionRow(
                meeting_id=meeting.id,
                decision=d.get("decision"),
                reason=d.get("reason"),
                confidence=d.get("confidence"),
            ))

        for a in (state.get("action_items") or []):
            db.add(ActionItemRow(
                meeting_id=meeting.id,
                task=a.get("task"),
                owner=a.get("owner"),
                deadline=a.get("deadline"),
                priority=a.get("priority"),
                status=a.get("status", "unknown"),
            ))

        email = state.get("follow_up_email")
        if email:
            db.add(EmailDraftRow(
                meeting_id=meeting.id,
                subject=email.get("subject", ""),
                body=email.get("body", ""),
                recipients=email.get("recipients", []),
                status=email.get("status", "draft"),
            ))

        for c in (state.get("calendar_suggestions") or []):
            db.add(CalendarSuggestionRow(
                meeting_id=meeting.id,
                title=c.get("title"),
                date=c.get("date"),
                time=c.get("time"),
                attendees=c.get("attendees", []),
                purpose=c.get("purpose", ""),
                status=c.get("status", "pending_approval"),
            ))

        for entry in (state.get("audit_log") or []):
            db.add(AuditLogRow(
                meeting_id=meeting.id,
                action_type=entry.get("action_id", "unknown"),
                status=entry.get("status"),
                details=entry.get("details"),
            ))

        db.commit()
        return meeting.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
