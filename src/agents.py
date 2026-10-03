from typing import Literal
from pydantic import BaseModel, Field
from .llm import get_llm
from .kb import retrieve
from .state import SupportState


# ---------- structured outputs ----------
class Classification(BaseModel):
    category: Literal["billing", "technical", "complaint", "general"]
    priority: Literal["low", "medium", "high"]
    sentiment: Literal["positive", "neutral", "negative"]
    summary: str = Field(description="One short sentence summarising the query")


class Reply(BaseModel):
    reply: str = Field(description="Email body to the customer, max 120 words")
    resolved: bool = Field(description="True only if the knowledge base clearly answers the question")
    confidence: int = Field(description="0-100")


class Escalation(BaseModel):
    ticket_summary: str
    suggested_action: str
    acknowledgement: str = Field(description="Short email (max 60 words) telling the customer a human will contact them within 24 hours")


# ---------- Agent 1: Classifier ----------
CLASSIFIER_PROMPT = """You are Agent 1, the Query Classifier of a customer support desk.
Classify the customer's message.
- billing: refunds, invoices, payments, charges
- technical: errors, bugs, login, app/website problems
- complaint: angry/unhappy customers, rude staff, repeated failures, legal threats
- general: everything else
priority=high if the customer is angry, mentions legal action, fraud, money lost, or the service is completely down."""


def classifier_agent(state: SupportState) -> dict:
    llm = get_llm(0).with_structured_output(Classification)
    r = llm.invoke([("system", CLASSIFIER_PROMPT),
                    ("human", f"Subject: {state.get('subject','')}\nMessage: {state['message']}")])
    return {"category": r.category, "priority": r.priority, "sentiment": r.sentiment, "summary": r.summary,
            "trace": [f"Agent 1 (Classifier): category={r.category}, priority={r.priority}, sentiment={r.sentiment}"]}


# ---------- Agent 2: Reply generator (RAG over KB) ----------
REPLY_PROMPT = """You are Agent 2, the Reply Writer of a customer support desk.
Answer ONLY using the KNOWLEDGE BASE provided. Never invent policies, prices, dates or promises.
Be polite, address the customer by name, keep it under 120 words, sign off as "SupportSync Support Team".
If the knowledge base does not clearly answer the question set resolved=false and confidence below 60."""


def reply_agent(state: SupportState) -> dict:
    kb = retrieve(state["message"], state.get("category"))
    llm = get_llm(0.3).with_structured_output(Reply)
    r = llm.invoke([("system", REPLY_PROMPT),
                    ("human", f"Customer name: {state['name']}\nCategory: {state['category']}\n"
                              f"Message: {state['message']}\n\nKNOWLEDGE BASE:\n{kb}")])
    return {"kb_context": kb, "reply": r.reply, "resolved": r.resolved, "confidence": r.confidence,
            "trace": [f"Agent 2 (Reply): resolved={r.resolved}, confidence={r.confidence}"]}


# ---------- Agent 3: Escalation ----------
ESCALATION_PROMPT = """You are Agent 3, the Escalation Agent of a customer support desk.
Prepare a hand-off for a human support agent: a 2-3 sentence ticket summary (what happened, what the customer wants),
one concrete suggested next action, and a short polite acknowledgement email for the customer signed "SupportSync Support Team"."""


def escalation_agent(state: SupportState) -> dict:
    llm = get_llm(0.2).with_structured_output(Escalation)
    r = llm.invoke([("system", ESCALATION_PROMPT),
                    ("human", f"Customer: {state['name']} ({state['email']})\nCategory: {state['category']}\n"
                              f"Priority: {state['priority']}\nSentiment: {state['sentiment']}\nMessage: {state['message']}")])
    return {"ticket_summary": r.ticket_summary, "suggested_action": r.suggested_action,
            "acknowledgement": r.acknowledgement,
            "trace": ["Agent 3 (Escalation): ticket summary prepared"]}
