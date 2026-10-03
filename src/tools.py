"""Side-effect tools: send email, create ticket, log. DRY_RUN=true keeps everything local."""
import csv, json, os, smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTBOX = ROOT / "outbox"
TICKET_FIELDS = ["ticket_id", "created_at", "customer", "email", "category", "priority", "sentiment",
                 "summary", "suggested_action", "status", "assigned_to"]
LOG_FIELDS = ["ticket_id", "received_at", "customer", "email", "category", "priority", "status", "message"]


def send_email(to: str, subject: str, body: str) -> str:
    if os.getenv("DRY_RUN", "true").lower() == "true":
        OUTBOX.mkdir(exist_ok=True)
        with open(OUTBOX / "outbox.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"time": datetime.now().isoformat(), "to": to, "subject": subject, "body": body}, ensure_ascii=False) + "\n")
        return f"[DRY_RUN] email saved for {to}"
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = os.environ["SMTP_USER"], to, subject
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_APP_PASSWORD"])
        s.send_message(msg)
    return f"email sent to {to}"


def _append(path: Path, fields: list, row: dict):
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(row)


def create_ticket(row: dict) -> str:
    _append(DATA / "tickets.csv", TICKET_FIELDS, row)
    return f"ticket {row['ticket_id']} created"


def log_resolved(row: dict) -> str:
    _append(DATA / "log.csv", LOG_FIELDS, row)
    return f"logged {row['ticket_id']}"
