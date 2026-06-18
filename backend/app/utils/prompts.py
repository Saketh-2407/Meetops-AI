SUMMARY_PROMPT = """You are an executive meeting analyst.
Summarize the meeting clearly for a busy engineering manager.

Produce:
- meeting_title: a short descriptive title
- executive_summary: 3-5 sentence summary
- key_points: the most important points discussed
- risks_or_blockers: explicit risks, blockers, or concerns raised (empty list if none)

Only use information present in the transcript. Do not invent content.

Transcript:
{transcript}
"""

DECISION_PROMPT = """Extract only clear, explicit decisions made in this meeting.
Do not invent decisions. If something was merely discussed but not decided, omit it.
For each decision give the decision text, an optional reason, and a confidence
score between 0 and 1.

Transcript:
{transcript}
"""

ACTION_PROMPT = """Extract action items from the meeting.

Rules:
- Only extract tasks that are actually mentioned or strongly implied.
- Identify the owner if stated; otherwise leave it null. Do not invent owners.
- Identify the deadline if stated; keep the original wording if vague.
- Set priority to one of: low, medium, high, urgent.
- Set is_engineering to true only for software engineering work (bug fixes,
  code changes, builds, deployments, infra/API/testing work) that belongs in
  an issue tracker. Set it to false for everything else (scheduling, business,
  marketing, generic follow-ups, etc.).

Transcript:
{transcript}
"""

EMAIL_PROMPT = """Write a professional follow-up email after this meeting.

Include:
- A short thank you
- A summary of the decisions
- Action items with owners and deadlines
- Clear next steps

Provide a subject, body, and recipients (empty list if unknown).

Transcript:
{transcript}

Decisions:
{decisions}

Action items:
{action_items}
"""

CALENDAR_PROMPT = """Suggest calendar events or follow-up meetings based on the transcript.
Only suggest an event if the meeting clearly implies one. Do not invent events.
For each, give a title, optional date, optional time, attendees, and purpose.

Transcript:
{transcript}

Action items:
{action_items}
"""

FINAL_REPORT_PROMPT = """Create a clean Markdown meeting report using exactly these sections:

# Meeting Report
## Executive Summary
## Key Points
## Key Decisions
## Action Items
## Risks / Blockers
## Suggested Follow-ups
## Draft Follow-up Email

Use only the data provided below.

Executive summary:
{executive_summary}

Key points:
{key_points}

Decisions:
{decisions}

Action items (with approval status):
{action_items}

Risks / blockers:
{risks}

Calendar suggestions:
{calendar}

Follow-up email:
{email}
"""
