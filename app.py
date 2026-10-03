"""Streamlit demo UI:  streamlit run app.py"""
import pandas as pd
import streamlit as st
from pathlib import Path
from src.graph import build_graph, run_query

st.set_page_config(page_title="SupportSync AI", page_icon="🎧", layout="wide")
st.title("🎧 SupportSync AI - Multi-Agent Support Desk")
st.caption("LangGraph • Gemini/OpenAI • FAQ knowledge base • automatic ticket escalation")


@st.cache_resource
def get_graph():
    return build_graph()


left, right = st.columns(2)
with left:
    name = st.text_input("Customer name", "Ali Khan")
    email = st.text_input("Customer email", "ali@example.com")
    examples = pd.read_csv("data/test_queries.csv")["message"].tolist()
    pick = st.selectbox("Load a sample query", ["(write my own)"] + examples)
    message = st.text_area("Customer message", "" if pick == "(write my own)" else pick, height=140)
    go = st.button("Process query", type="primary")

if go and message.strip():
    with st.spinner("Agents are working..."):
        res = run_query(name, email, message, graph=get_graph())
    with right:
        st.subheader("Result")
        c1, c2, c3 = st.columns(3)
        c1.metric("Category", res["category"])
        c2.metric("Priority", res["priority"])
        c3.markdown(f"**Status**\n\n{res['status']}")
        st.markdown("**Agent trace**")
        for t in res["trace"]:
            st.write("•", t)
        if res["status"] == "Resolved by AI":
            st.success(res["reply"])
        else:
            st.warning(f"**Ticket {res['ticket_id']}**\n\n{res['ticket_summary']}\n\n*Suggested action:* {res['suggested_action']}")
            st.info(f"Customer acknowledgement:\n\n{res['acknowledgement']}")

st.divider()
t1, t2, t3 = st.tabs(["Tickets (escalated)", "Log (auto-resolved)", "Outbox (emails)"])
for tab, path in ((t1, "data/tickets.csv"), (t2, "data/log.csv")):
    with tab:
        if Path(path).exists():
            st.dataframe(pd.read_csv(path))
        else:
            st.write("Nothing yet.")
with t3:
    p = Path("outbox/outbox.jsonl")
    if p.exists():
        st.dataframe(pd.read_json(p, lines=True))
    else:
        st.write("Nothing yet.")