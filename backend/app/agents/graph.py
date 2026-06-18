from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from app.agents.state import MeetingState
from app.agents.summary_agent import summary_agent
from app.agents.decision_agent import decision_agent
from app.agents.action_agent import action_agent
from app.agents.email_agent import email_agent
from app.agents.calendar_agent import calendar_agent
from app.agents.approval_agent import human_approval, execute_actions
from app.agents.final_report_agent import final_report_agent


def build_meeting_graph(checkpointer=None):
    """Compile the meeting graph with the given checkpointer.

    Pass a PostgresSaver for durable checkpointing (Phase 2+).
    Defaults to InMemorySaver so the module can be imported safely before
    the database is reachable (e.g. during testing or first import).
    The lifespan in main.py replaces meeting_graph with a PostgresSaver
    instance once the DB connection is established.
    """
    if checkpointer is None:
        checkpointer = InMemorySaver()

    graph = StateGraph(MeetingState)

    graph.add_node("summary_agent", summary_agent)
    graph.add_node("decision_agent", decision_agent)
    graph.add_node("action_agent", action_agent)
    graph.add_node("email_agent", email_agent)
    graph.add_node("calendar_agent", calendar_agent)
    graph.add_node("human_approval", human_approval)
    graph.add_node("execute_actions", execute_actions)
    graph.add_node("final_report_agent", final_report_agent)

    graph.set_entry_point("summary_agent")
    graph.add_edge("summary_agent", "decision_agent")
    graph.add_edge("decision_agent", "action_agent")
    graph.add_edge("action_agent", "email_agent")
    graph.add_edge("email_agent", "calendar_agent")
    graph.add_edge("calendar_agent", "human_approval")
    graph.add_edge("human_approval", "execute_actions")
    graph.add_edge("execute_actions", "final_report_agent")
    graph.add_edge("final_report_agent", END)

    return graph.compile(checkpointer=checkpointer)


# Starts with InMemorySaver; replaced by PostgresSaver in the FastAPI lifespan.
meeting_graph = build_meeting_graph()
