"""CLI:  python main.py            -> runs all test queries
        python main.py "my message here" you@example.com "Your Name"
"""
import sys
import pandas as pd
from src.graph import build_graph, run_query


def show(res):
    print(f"\n=== {res['ticket_id']} | {res['category']} | {res['priority']} | {res['status']} ===")
    for t in res["trace"]:
        print("  ->", t)
    if res.get("status") == "Resolved by AI":
        print("  REPLY:", res["reply"][:300])


if __name__ == "__main__":
    graph = build_graph()
    if len(sys.argv) > 1:
        msg = sys.argv[1]
        email = sys.argv[2] if len(sys.argv) > 2 else "customer@example.com"
        name = sys.argv[3] if len(sys.argv) > 3 else "Customer"
        show(run_query(name, email, msg, graph=graph))
    else:
        for _, r in pd.read_csv("data/test_queries.csv").iterrows():
            print(f"\nQUERY: {r['message']}  (expected: {r['expected_path']})")
            show(run_query(r["name"], r["email"], r["message"], graph=graph))
