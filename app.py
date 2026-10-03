"""SupportSync AI - interactive Streamlit UI.   Run:  python -m streamlit run app.py"""
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.graph import build_graph

st.set_page_config(page_title="SupportSync AI", page_icon="🎧", layout="wide")

TICKETS, LOG, OUTBOX = Path("data/tickets.csv"), Path("data/log.csv"), Path("outbox/outbox.jsonl")

# ---------------------------------------------------------------- styling
st.markdown("""
<style>
.hero{padding:26px 30px;border-radius:18px;background:linear-gradient(120deg,#4f46e5,#7c3aed 55%,#db2777);color:#fff;margin-bottom:18px}
.hero h1{margin:0;font-size:2.1rem;color:#fff}
.hero p{margin:6px 0 0;opacity:.92;font-size:1.02rem}
.pipe{display:flex;gap:10px;align-items:stretch;margin:6px 0 14px}
.step{flex:1;padding:12px 14px;border-radius:14px;border:2px solid #e5e7eb;background:#fafafa;transition:all .3s}
.step .t{font-weight:700;font-size:.95rem}.step .d{font-size:.8rem;color:#6b7280}
.step.active{border-color:#6366f1;background:#eef2ff;box-shadow:0 0 0 4px #e0e7ff}
.step.done{border-color:#10b981;background:#ecfdf5}
.step.skipped{opacity:.45;border-style:dashed}
.arrow{align-self:center;font-size:1.4rem;color:#9ca3af}
.badge{display:inline-block;padding:4px 12px;border-radius:999px;font-weight:700;font-size:.85rem;margin-right:6px}
.card{padding:16px 18px;border-radius:14px;border:1px solid #e5e7eb;background:#fff;margin-top:10px}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero"><h1>🎧 SupportSync AI</h1>
<p>Multi-agent customer support desk &nbsp;•&nbsp; LangGraph &nbsp;•&nbsp; Gemini &nbsp;•&nbsp; FAQ knowledge base &nbsp;•&nbsp; automatic ticket escalation</p></div>
""", unsafe_allow_html=True)


@st.cache_resource
def get_graph():
    return build_graph()


def read_csv(p):
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


CAT_COL = {"billing": "#f59e0b", "technical": "#3b82f6", "complaint": "#ef4444", "general": "#10b981"}
PRI_COL = {"low": "#10b981", "medium": "#f59e0b", "high": "#ef4444"}
SENT_ICON = {"positive": "😊", "neutral": "😐", "negative": "😠"}


def badge(text, color):
    return f'<span class="badge" style="background:{color}22;color:{color};border:1px solid {color}">{text}</span>'


def pipeline_html(s):
    names = [("classify", "🧭 Agent 1", "Classifier"), ("reply", "💬 Agent 2", "Reply Writer (KB)"),
             ("escalation_agent", "🚨 Agent 3", "Escalation"), ("action", "⚡ Action", "Email / Ticket")]
    out = '<div class="pipe">'
    for i, (k, t, d) in enumerate(names):
        out += f'<div class="step {s.get(k, "")}"><div class="t">{t}</div><div class="d">{d}</div></div>'
        if i < len(names) - 1:
            out += '<div class="arrow">➜</div>'
    return out + "</div>"


# ---------------------------------------------------------------- samples
SAMPLES = {
    "🔑 Password reset": ("Ali Khan", "ali@example.com", "I forgot my password, how can I reset it?"),
    "🧾 Need invoice": ("Sara Ahmed", "sara@example.com", "Please send me my invoice for last month."),
    "💥 App crashing": ("Bilal Sheikh", "bilal@example.com", "The app crashes every time I open it since yesterday's update."),
    "😡 Angry complaint": ("Hina Malik", "hina@example.com", "I was charged twice and nobody is replying. This is unacceptable, I want my money back or I will go to court!"),
    "🌍 Not in FAQ": ("Ayesha Noor", "ayesha@example.com", "Can I change the delivery address of my custom order placed in Dubai branch?"),
}
for k, v in (("name", "Ali Khan"), ("email", "ali@example.com"), ("msg", "")):
    st.session_state.setdefault(k, v)


def load_sample(label):
    n, e, m = SAMPLES[label]
    st.session_state.update(name=n, email=e, msg=m)


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("⚙️ Control panel")
    st.caption("Click a scenario to load it, then press **Process query**.")
    for label in SAMPLES:
        st.button(label, on_click=load_sample, args=(label,), width="stretch")
    st.divider()
    t, l = read_csv(TICKETS), read_csv(LOG)
    st.metric("Auto-resolved by AI", len(l))
    st.metric("Escalated to humans", len(t))
    total = len(t) + len(l)
    if total:
        st.progress(len(l) / total, text=f"{round(100 * len(l) / total)}% handled without a human")
    st.divider()
    st.markdown("**Routing rules**\n- complaint / high priority → human\n- KB can't answer → human\n- otherwise → AI replies")

tab_live, tab_dash, tab_data = st.tabs(["🎬 Live Desk", "📊 Dashboard", "🗂️ Tickets & Emails"])

# ---------------------------------------------------------------- live desk
with tab_live:
    left, right = st.columns([1, 1.25], gap="large")
    with left:
        st.subheader("📥 Incoming customer message")
        st.text_input("Customer name", key="name")
        st.text_input("Customer email", key="email")
        st.text_area("Message", key="msg", height=150, placeholder="Type a customer query or pick a scenario from the sidebar...")
        go = st.button("🚀 Process query", type="primary", width="stretch")

    with right:
        st.subheader("🤖 Agents at work")
        pipe_box = st.empty()
        pipe_box.markdown(pipeline_html({}), unsafe_allow_html=True)
        log_box = st.empty()

        if go:
            if not st.session_state.msg.strip():
                st.warning("Please write a message first.")
            else:
                init = {"ticket_id": "TKT-" + datetime.now().strftime("%m%d%H%M%S%f")[:12],
                        "name": st.session_state.name, "email": st.session_state.email,
                        "subject": "Support Request", "message": st.session_state.msg, "trace": []}
                state, stages, trace = dict(init), {}, []
                try:
                    pipe_box.markdown(pipeline_html({"classify": "active"}), unsafe_allow_html=True)
                    for upd in get_graph().stream(init, stream_mode="updates"):
                        for node, out in upd.items():
                            state.update({k: v for k, v in out.items() if k != "trace"})
                            trace += out.get("trace", [])
                            stages["action" if node in ("send_reply", "create_ticket") else node] = "done"
                            nxt = {"classify": "reply" if not (state["category"] == "complaint" or state["priority"] == "high") else "escalation_agent",
                                   "reply": "action" if state.get("resolved") and state.get("confidence", 0) >= 60 else "escalation_agent",
                                   "escalation_agent": "action"}.get(node)
                            if nxt and nxt not in stages:
                                stages[nxt] = "active"
                            pipe_box.markdown(pipeline_html(stages), unsafe_allow_html=True)
                            log_box.markdown("\n\n".join(f"✅ {x}" for x in trace))
                            time.sleep(0.5)
                    for k in ("reply", "escalation_agent"):
                        stages.setdefault(k, "skipped")
                    pipe_box.markdown(pipeline_html(stages), unsafe_allow_html=True)
                    state["trace"] = trace
                    st.session_state.last = state
                    if state.get("status") == "Resolved by AI":
                        st.balloons()
                    else:
                        st.toast("Ticket created and support team alerted", icon="🚨")
                except Exception as e:  # network / quota / key problems
                    st.error(f"Something went wrong: {e}")

        res = st.session_state.get("last")
        if res and not go:
            pipe_box.markdown(pipeline_html({"classify": "done", "reply": "done" if res.get("reply") else "skipped",
                                             "escalation_agent": "done" if res.get("status") == "Escalated" else "skipped",
                                             "action": "done"}), unsafe_allow_html=True)

        if res:
            st.markdown(
                badge(res["category"].upper(), CAT_COL.get(res["category"], "#6b7280"))
                + badge("PRIORITY: " + res["priority"].upper(), PRI_COL.get(res["priority"], "#6b7280"))
                + badge(f'{SENT_ICON.get(res["sentiment"], "")} {res["sentiment"]}', "#6366f1")
                + badge(res["status"], "#10b981" if res["status"] == "Resolved by AI" else "#ef4444"),
                unsafe_allow_html=True)
            st.caption(f'🎫 {res["ticket_id"]}  •  💡 {res.get("summary", "")}')
            with st.chat_message("user"):
                st.write(res["message"])
            if res["status"] == "Resolved by AI":
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(res["reply"])
                    st.caption(f'Confidence {res["confidence"]}%  •  sent to {res["email"]}')
                with st.expander("📚 Knowledge-base entries the agent used"):
                    st.text(res.get("kb_context", ""))
            else:
                with st.chat_message("assistant", avatar="🚨"):
                    st.markdown(f'**Escalated to a human agent**\n\n{res["ticket_summary"]}')
                    st.info(f'**Suggested action:** {res["suggested_action"]}')
                with st.expander("✉️ Acknowledgement sent to customer"):
                    st.write(res["acknowledgement"])
                if res.get("kb_context") is not None and res.get("confidence") is not None:
                    st.caption(f'Agent 2 confidence was {res.get("confidence")}%')

# ---------------------------------------------------------------- dashboard
with tab_dash:
    t, l = read_csv(TICKETS), read_csv(LOG)
    total = len(t) + len(l)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total queries", total)
    c2.metric("Auto-resolved", len(l))
    c3.metric("Escalated", len(t))
    c4.metric("AI resolution rate", f"{round(100 * len(l) / total)}%" if total else "-")
    if total:
        both = pd.concat([d[["category", "priority"]] for d in (t, l) if len(d)])
        a, b = st.columns(2)
        with a:
            st.markdown("**Queries by category**")
            st.bar_chart(both["category"].value_counts())
        with b:
            st.markdown("**Queries by priority**")
            st.bar_chart(both["priority"].value_counts())
    else:
        st.info("Process a few queries in the Live Desk tab and the charts will appear here.")

# ---------------------------------------------------------------- data
with tab_data:
    t1, t2, t3 = st.tabs(["🚨 Tickets (escalated)", "✅ Log (auto-resolved)", "✉️ Outbox (emails)"])
    with t1:
        df = read_csv(TICKETS)
        if len(df):
            st.dataframe(df, width="stretch")
            st.download_button("⬇️ Download tickets.csv", df.to_csv(index=False), "tickets.csv", "text/csv")
        else:
            st.write("No tickets yet.")
    with t2:
        df = read_csv(LOG)
        if len(df):
            st.dataframe(df, width="stretch")
        else:
            st.write("Nothing logged yet.")
    with t3:
        if OUTBOX.exists():
            st.dataframe(pd.read_json(OUTBOX, lines=True), width="stretch")
        else:
            st.write("No emails yet.")
    if st.button("🧹 Reset demo data"):
        for p in (TICKETS, LOG, OUTBOX):
            p.unlink(missing_ok=True)
        st.session_state.pop("last", None)
        st.rerun()
