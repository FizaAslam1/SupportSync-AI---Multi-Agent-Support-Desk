import os
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from .state import SupportState
from .agents import classifier_agent, reply_agent, escalation_agent
from . import tools

CONFIDENCE_THRESHOLD = 60


# ---------- action nodes ----------
def send_reply_node(state: SupportState) -> dict:
    res = tools.send_email(state["email"], f"Re: {state.get('subject', 'Your request')}", state["reply"])
    tools.log_resolved({"ticket_id": state["ticket_id"], "received_at": datetime.now().isoformat(),
                        "customer": state["name"], "email": state["email"], "category": state["category"],
                        "priority": state["priority"], "status": "Resolved by AI", "message": state["message"]})
    return {"status": "Resolved by AI", "trace": [f"Send reply: {res}"]}


def ticket_node(state: SupportState) -> dict:
    t = tools.create_ticket({
        "ticket_id": state["ticket_id"], "created_at": datetime.now().isoformat(), "customer": state["name"],
        "email": state["email"], "category": state["category"], "priority": state["priority"],
        "sentiment": state["sentiment"], "summary": state["ticket_summary"],
        "suggested_action": state["suggested_action"], "status": "Open", "assigned_to": ""})
    team = os.getenv("SUPPORT_TEAM_EMAIL", "support-team@yourcompany.com")
    a = tools.send_email(
        team, f"[{state['priority'].upper()}] Escalated ticket {state['ticket_id']}",
        f"Category: {state['category']}\nCustomer: {state['name']} ({state['email']})\n\n"
        f"Summary: {state['ticket_summary']}\n\nSuggested action: {state['suggested_action']}\n\n"
        f"Original message:\n{state['message']}")
    c = tools.send_email(state["email"], f"We received your request ({state['ticket_id']})", state["acknowledgement"])
    return {"status": "Escalated", "trace": [f"Ticket: {t}", f"Team alert: {a}", f"Customer ack: {c}"]}


# ---------- routers ----------
def route_after_classify(state: SupportState) -> str:
    # Complaints / high priority skip auto-reply and go straight to a human
    if state["category"] == "complaint" or state["priority"] == "high":
        return "escalate"
    return "reply"


def route_after_reply(state: SupportState) -> str:
    if (not state["resolved"]) or state["confidence"] < CONFIDENCE_THRESHOLD:
        return "escalate"
    return "send"


def build_graph():
    g = StateGraph(SupportState)
    g.add_node("classify", classifier_agent)
    g.add_node("reply", reply_agent)
    g.add_node("send_reply", send_reply_node)
    g.add_node("escalation_agent", escalation_agent)
    g.add_node("create_ticket", ticket_node)

    g.add_edge(START, "classify")
    g.add_conditional_edges("classify", route_after_classify, {"reply": "reply", "escalate": "escalation_agent"})
    g.add_conditional_edges("reply", route_after_reply, {"send": "send_reply", "escalate": "escalation_agent"})
    g.add_edge("escalation_agent", "create_ticket")
    g.add_edge("send_reply", END)
    g.add_edge("create_ticket", END)
    return g.compile()


def run_query(name: str, email: str, message: str, subject: str = "Support Request", graph=None) -> dict:
    graph = graph or build_graph()
    init = {"ticket_id": "TKT-" + datetime.now().strftime("%m%d%H%M%S%f")[:12], "name": name, "email": email,
            "subject": subject, "message": message, "trace": []}
    return graph.invoke(init)
