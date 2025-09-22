import os, sys, base64, textwrap, re
from email.mime.text import MIMEText
from email.utils import formataddr

# ---- Gmail API auth ----
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

import requests  # for Ollama and (optionally) HTTP calls

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
]

# ---------------- Gmail OAuth / Service ----------------
def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists("credentials.json"):
                print("ERROR: credentials.json not found. Put your OAuth client JSON here.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            # Opens a browser for consent on first run
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

# ---------------- LLM Draft (Ollama, with fallback) ----------------
def ollama_generate(prompt, model="llama3.1", host="http://localhost:11434"):
    try:
        r = requests.post(
            f"{host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        r.raise_for_status()
        out = r.json().get("response", "").strip()
        return out or None
    except Exception:
        return None

SYSTEM_SPEC = """You are InboxPilot, an email drafting assistant.
Always return a polished, professional email body only, following the user's instruction.
Do not include extra commentary or metadata.
"""

PROMPT_TMPL = """{system}

EMAIL TO ANSWER (raw):
---
{email_text}
---

USER INSTRUCTION for reply style/intent:
---
{instruction}
---

TASK:
1) Start with an appropriate greeting (e.g., "Hi Dr. Smith,") if a name is obvious; else "Hi,".
2) Draft a concise, helpful reply that addresses all key points.
3) End with a short sign-off with the sender's first name: "Best, Krish".

Return ONLY the final email body (no extra commentary).
"""

def draft_reply_with_ai(email_text: str, instruction: str) -> str:
    prompt = PROMPT_TMPL.format(
        system=SYSTEM_SPEC, email_text=email_text.strip(), instruction=instruction.strip()
    )
    out = ollama_generate(prompt)
    if out:
        return out.strip()

    # Fallback template if Ollama not running
    return textwrap.dedent(f"""\
    Hi,

    Thanks for reaching out. {instruction.strip().rstrip('.')}.
    Here are the key points I’d like to address:

    - [Point 1]
    - [Point 2]

    Please let me know if there’s anything else needed.

    Best,
    Krish
    """).strip()

# ---------------- Minimal field extraction ----------------
SENDER_RE = re.compile(r"From:\s*(.+?)\s*<([^>]+)>|From:\s*([^<\n]+@\S+)", re.IGNORECASE)
SUBJ_RE   = re.compile(r"Subject:\s*(.+)", re.IGNORECASE)

def guess_sender_and_subject(email_text: str):
    sender_email = None
    sender_name = None
    m = SENDER_RE.search(email_text)
    if m:
        if m.group(2):  # "Name <email>"
            sender_name = (m.group(1) or "").strip().strip('"')
            sender_email = m.group(2).strip()
        elif m.group(3):  # just email
            sender_email = m.group(3).strip()

    m2 = SUBJ_RE.search(email_text)
    subject = m2.group(1).strip() if m2 else "Re: Your email"
    if subject and not subject.lower().startswith("re:"):
        subject = "Re: " + subject
    return sender_name, sender_email, subject

# ---------------- Gmail helpers ----------------
def build_message(to_email: str, subject: str, body: str, from_name="Krish"):
    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = to_email
    msg["Subject"] = subject
    # Gmail sets actual From; adding a display name is optional:
    if from_name:
        msg["From"] = formataddr((from_name, ""))  # empty email lets Gmail use account
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}

def create_draft(service, user_id: str, message):
    return service.users().drafts().create(userId=user_id, body={"message": message}).execute()

def send_message(service, user_id: str, message):
    return service.users().messages().send(userId=user_id, body=message).execute()

# ---------------- CLI workflow ----------------
def main():
    print("Paste the FULL email content you received. End with a single line containing only 'END':\n")
    lines = []
    for line in sys.stdin:
        if line.strip() == "END":
            break
        lines.append(line.rstrip("\n"))
    email_text = "\n".join(lines).strip()
    if not email_text:
        print("No email text provided. Exiting.")
        return

    print("\nHow do you want to respond? (e.g., 'polite decline', 'accept and ask for timeline', 'request more details about X')\n> ", end="")
    instruction = input().strip()

    print("\nDrafting with AI...\n")
    body = draft_reply_with_ai(email_text, instruction)
    print("=" * 70)
    print(body)
    print("=" * 70)

    # Guess recipient + subject (user can override)
    _, sender_email, subject = guess_sender_and_subject(email_text)
    print(f"\nGuessed To: {sender_email or '(unknown)'}   Subject: {subject}")
    to_override = input("Change recipient email? (press Enter to keep / type new): ").strip()
    if to_override:
        sender_email = to_override
    if not sender_email:
        sender_email = input("Recipient email required (type now): ").strip()

    subj_override = input("Change subject? (press Enter to keep / type new): ").strip()
    if subj_override:
        subject = subj_override

    action = input("\nType 'draft' to add as Gmail Draft, 'send' to send now, or 'quit' to exit: ").strip().lower()
    if action not in {"draft", "send"}:
        print("Exiting without Gmail action.")
        return

    service = get_gmail_service()
    msg = build_message(sender_email, subject, body)

    if action == "draft":
        dr = create_draft(service, "me", msg)
        print(f"\n✅ Draft created. Draft ID: {dr.get('id')}")
    else:
        sent = send_message(service, "me", msg)
        print(f"\n✅ Email sent. Message ID: {sent.get('id')}")

if __name__ == "__main__":
    main()