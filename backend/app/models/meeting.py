from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship

from app.database import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    transcript = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    decisions = relationship("DecisionRow", back_populates="meeting")
    action_items = relationship("ActionItemRow", back_populates="meeting")
    email_drafts = relationship("EmailDraftRow", back_populates="meeting")
    calendar_suggestions = relationship("CalendarSuggestionRow", back_populates="meeting")
    audit_logs = relationship("AuditLogRow", back_populates="meeting")


class DecisionRow(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    decision = Column(Text)
    reason = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)

    meeting = relationship("Meeting", back_populates="decisions")


class ActionItemRow(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    task = Column(Text)
    owner = Column(String, nullable=True)
    deadline = Column(String, nullable=True)
    priority = Column(String)
    status = Column(String, default="pending_approval")
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="action_items")


class EmailDraftRow(Base):
    __tablename__ = "email_drafts"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    subject = Column(String)
    body = Column(Text)
    recipients = Column(JSON, default=list)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="email_drafts")


class CalendarSuggestionRow(Base):
    __tablename__ = "calendar_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    title = Column(String)
    date = Column(String, nullable=True)
    time = Column(String, nullable=True)
    attendees = Column(JSON, default=list)
    purpose = Column(Text)
    status = Column(String, default="pending_approval")
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="calendar_suggestions")


class AuditLogRow(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    action_type = Column(String)
    status = Column(String)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="audit_logs")
