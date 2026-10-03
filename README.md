# SupportSync AI - Multi-Agent Customer Support Desk (LangGraph)
Category: Business Process Automation (Multi-Agent Systems + Agentic AI)
Stack: Python - LangGraph - Gemini (or OpenAI) - CSV/Google-Sheets-ready tickets - Gmail SMTP - Streamlit UI

## Folder
SupportSync-LG/
  src/state.py     shared graph state
  src/agents.py    Agent 1 Classifier, Agent 2 Reply (RAG), Agent 3 Escalation
  src/kb.py        FAQ retriever (data/knowledge_base.csv)
  src/tools.py     send_email, create_ticket, log_resolved
  src/graph.py     LangGraph workflow + conditional routing
  main.py          CLI runner (runs the 7 test queries)
  app.py           Streamlit demo UI
  SupportSync_LangGraph.ipynb   Colab/Jupyter notebook (self-contained)
  data/            knowledge_base.csv, test_queries.csv
  docs/            demo script, submission text

## Graph
START -> classify (Agent 1)
   complaint OR high priority -> escalation_agent (Agent 3) -> create_ticket -> END
   else -> reply (Agent 2, answers only from KB)
        resolved AND confidence >= 60 -> send_reply -> END
        else -> escalation_agent (Agent 3) -> create_ticket -> END

## Run locally
1. python -m venv venv && venv\Scripts\activate      (Windows)   |  source venv/bin/activate (Mac/Linux)
2. pip install -r requirements.txt
3. copy .env.example to .env and put your GOOGLE_API_KEY (free: aistudio.google.com)
4. python main.py                      # all 7 test queries
   python main.py "I forgot my password" you@example.com "Ali"
   streamlit run app.py                # demo UI
DRY_RUN=true (default) saves emails to outbox/outbox.jsonl instead of sending. For real Gmail: DRY_RUN=false, SMTP_USER and an App Password.

## Run in Google Colab
Upload SupportSync_LangGraph.ipynb, paste your Gemini key in cell 2, Run all.

## Outputs created at runtime
data/tickets.csv (escalated), data/log.csv (auto-resolved), outbox/outbox.jsonl (emails)
