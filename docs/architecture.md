# Architecture (LangGraph)

           +-----------+
 START --> | classify  |  Agent 1: category / priority / sentiment (structured output)
           +-----+-----+
     complaint or high priority          otherwise
           |                                 |
           |                          +------v------+
           |                          |   reply     |  Agent 2: retrieves FAQ entries, answers only from them
           |                          +------+------+
           |                   resolved & confidence>=60 |  else
           |                                 |           |
           v                                 v           v
   +------------------+               +------------+     |
   | escalation_agent |<--------------| send_reply |     |
   +--------+---------+  (else path)  +-----+------+     |
            v                               v            |
     +--------------+                      END            |
     | create_ticket|  ticket row + team alert + customer ack
     +------+-------+
            v
           END

Key ideas: shared typed state, conditional edges (agentic routing), structured output (Pydantic) so agents return reliable JSON,
tools separated from agents, confidence-based human hand-off.
