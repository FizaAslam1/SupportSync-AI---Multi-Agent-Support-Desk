import operator
from typing import Annotated, TypedDict


class SupportState(TypedDict, total=False):
    # input
    ticket_id: str
    name: str
    email: str
    subject: str
    message: str
    # Agent 1 output
    category: str      # billing | technical | complaint | general
    priority: str      # low | medium | high
    sentiment: str     # positive | neutral | negative
    summary: str
    # Agent 2 output
    kb_context: str
    reply: str
    resolved: bool
    confidence: int
    # Agent 3 output
    ticket_summary: str
    suggested_action: str
    acknowledgement: str
    # result
    status: str        # "Resolved by AI" | "Escalated"
    trace: Annotated[list, operator.add]
