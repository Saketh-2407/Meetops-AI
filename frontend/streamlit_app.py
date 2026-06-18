import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="MeetOps AI", layout="wide")
st.title("MeetOps AI")
st.caption("Agentic Meeting Summarizer & Action-Taking Assistant")

# Session state for the two-step approval flow.
st.session_state.setdefault("phase", "input")        # input -> approval -> done
st.session_state.setdefault("thread_id", None)
st.session_state.setdefault("analysis", None)
st.session_state.setdefault("final", None)
st.session_state.setdefault("source", "text")        # "text" or "audio"


def reset():
    st.session_state.phase = "input"
    st.session_state.thread_id = None
    st.session_state.analysis = None
    st.session_state.final = None
    st.session_state.source = "text"


# --- Phase 1: input ----------------------------------------------------------
if st.session_state.phase == "input":
    input_mode = st.radio("Input method", ["Paste transcript", "Upload audio"], horizontal=True)

    if input_mode == "Paste transcript":
        transcript = st.text_area(
            "Paste meeting transcript", height=300,
            placeholder="Paste your meeting transcript here...",
        )
        if st.button("Analyze Meeting", type="primary"):
            if not transcript.strip():
                st.warning("Please paste a transcript first.")
            else:
                with st.spinner("Running agents..."):
                    resp = requests.post(
                        f"{API_BASE}/analyze", json={"transcript": transcript}
                    )
                if resp.status_code != 200:
                    st.error(f"Backend error: {resp.status_code}")
                else:
                    data = resp.json()
                    st.session_state.analysis = data
                    st.session_state.thread_id = data.get("thread_id")
                    st.session_state.source = "text"
                    st.session_state.phase = "approval"
                    st.rerun()

    else:  # Upload audio
        st.info(
            "Transcription may contain errors — review the transcript "
            "carefully before approving any actions."
        )
        audio_file = st.file_uploader(
            "Upload a meeting recording", type=["mp3", "wav", "m4a", "mp4", "webm"],
        )
        if st.button("Transcribe & Analyze", type="primary"):
            if audio_file is None:
                st.warning("Please upload an audio file first.")
            else:
                with st.spinner("Transcribing audio and running agents..."):
                    resp = requests.post(
                        f"{API_BASE}/upload-audio",
                        files={"file": (audio_file.name, audio_file.getvalue())},
                    )
                if resp.status_code != 200:
                    st.error(f"Backend error: {resp.status_code}")
                else:
                    data = resp.json()
                    st.session_state.analysis = data
                    st.session_state.thread_id = data.get("thread_id")
                    st.session_state.source = "audio"
                    st.session_state.phase = "approval"
                    st.rerun()

# --- Phase 2: review & approve ----------------------------------------------
elif st.session_state.phase == "approval":
    data = st.session_state.analysis
    req = data.get("approval_request", {})

    if st.session_state.source == "audio":
        st.warning(
            "⚠️ This meeting was transcribed from audio. Transcription may "
            "contain errors — review the transcript below carefully before "
            "approving any actions."
        )
        with st.expander("Review transcribed text", expanded=True):
            st.write(data.get("transcript", ""))

    st.subheader("Executive Summary")
    st.write(data.get("executive_summary"))

    st.subheader("Decisions")
    st.json(data.get("decisions"))

    st.subheader("Review pending items")
    st.caption(
        "Approve or reject each item. Only approved items are executed — "
        "emails are created as Gmail drafts (never sent), calendar items "
        "are added to your calendar, and engineering tasks become GitHub "
        "issues, all only once approved."
    )

    decisions = {}
    for item in req.get("pending_actions", []):
        aid = item["id"]
        itype = item.get("type", "task")

        if itype == "email":
            st.markdown(f"**📧 Email draft:** {item.get('subject', '')}")
            with st.expander("View email body"):
                st.write(item.get("body", ""))
                st.caption(f"Recipients: {', '.join(item.get('recipients', [])) or '(none specified)'}")
        elif itype == "calendar":
            st.markdown(f"**📅 Calendar event:** {item.get('title', '')}")
            st.caption(
                f"Date: {item.get('date') or '-'} | Time: {item.get('time') or '-'} | "
                f"Attendees: {', '.join(item.get('attendees', [])) or '-'}"
            )
            st.caption(item.get("purpose", ""))
        elif itype == "github":
            st.markdown(f"**🐙 GitHub issue:** {item.get('task', '')}")
            st.caption(
                f"Owner: {item.get('owner') or '-'} | "
                f"Deadline: {item.get('deadline') or '-'} | "
                f"Priority: {item.get('priority')}"
            )
        else:
            label = f"**{item['task']}**  \n"
            label += f"Owner: {item.get('owner') or '-'} | "
            label += f"Deadline: {item.get('deadline') or '-'} | "
            label += f"Priority: {item.get('priority')}"
            st.markdown(label)

        choice = st.radio(
            "Decision", ["approved", "rejected"],
            key=f"dec_{aid}", horizontal=True, label_visibility="collapsed",
        )
        decisions[aid] = choice
        st.divider()

    col1, col2 = st.columns(2)
    if col1.button("Submit approvals", type="primary"):
        with st.spinner("Executing approved actions & generating report..."):
            resp = requests.post(
                f"{API_BASE}/resume",
                json={
                    "thread_id": st.session_state.thread_id,
                    "approval_decisions": decisions,
                },
            )
        if resp.status_code != 200:
            st.error(f"Backend error: {resp.status_code}")
        else:
            st.session_state.final = resp.json()
            st.session_state.phase = "done"
            st.rerun()
    if col2.button("Start over"):
        reset()
        st.rerun()

# --- Phase 3: results --------------------------------------------------------
elif st.session_state.phase == "done":
    final = st.session_state.final
    st.success("Workflow complete.")

    st.subheader("Final Report")
    st.markdown(final.get("final_report"))

    with st.expander("Executed actions"):
        st.json(final.get("executed_actions"))
    with st.expander("Audit log"):
        st.json(final.get("audit_log"))
    with st.expander("Final action item statuses"):
        st.json(final.get("action_items"))

    if st.button("Analyze another meeting"):
        reset()
        st.rerun()
