# 3-minute demo script
1. (20s) Problem: support teams answer the same questions all day; slow replies lose customers.
2. (20s) Show the workflow canvas: 3 agents.
3. (40s) Send test query #1 (password reset) -> show email arrived in inbox + row in Log tab.
4. (60s) Send test query #4 (angry double-charge complaint) -> show Agent 1 = complaint/high, ticket row in Tickets tab, alert email to team, acknowledgement to customer.
5. (20s) Send query #6 (not in KB) -> shows confidence fallback to human.
6. (20s) Impact: response time from hours to seconds, humans only handle complex cases.

# Likely judge questions
- How do you avoid hallucination? Agent 2 is restricted to the KB and returns a confidence score; low confidence escalates.
- Is it scalable? Yes, n8n queue mode; KB can move to a vector DB.
- Why not one agent? Separation of concerns, easier debugging, independent improvement.
- Data privacy? Only the message text goes to the LLM; credentials stay in n8n.
