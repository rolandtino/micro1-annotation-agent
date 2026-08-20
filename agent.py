import warnings
warnings.filterwarnings("ignore")

import json
import os
import hashlib
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from groq import Groq
from ddgs import DDGS

client = Groq()

MEMORY_FILE = "agent_memory.json"
MICRO1_LOG_FILE = "micro1_check_log.json"

# Reads your Gmail address and app password from environment variables,
# never hardcoded here, so this stays safe to upload to GitHub
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

# Edit this list any time your skills or focus areas change.
# The agent checks Micro1 search results against every item here.
# Kept broad on purpose so close matches (like "Evaluator" for "AI model evaluation") still get caught.
MY_SKILLS = [
    "electrical engineering",
    "control systems",
    "annotation",
    "annotator",
    "evaluator",
    "evaluation",
    "AI trainer",
    "data trainer",
    "technical writing",
    "prompt",
    "generalist",
    "software engineering",
    "computer engineering",
    "data analyst"
]


def web_search(query, max_results=4):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    if not results:
        return "No results found."
    formatted = ""
    for r in results:
        formatted += f"Title: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}\n\n"
    return formatted


def load_micro1_log():
    if os.path.exists(MICRO1_LOG_FILE):
        with open(MICRO1_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_checked": None, "last_hash": None, "last_result": ""}


def save_micro1_log(log):
    with open(MICRO1_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)


def hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def send_email_alert(subject, body):
    """
    Sends a simple email to yourself using Gmail's SMTP server.
    Requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD to be set as environment variables.
    Silently skips if those aren't set, so the agent doesn't crash if email isn't configured.
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("[email alert skipped: GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set]")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = GMAIL_ADDRESS

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print("[email alert sent]")
    except Exception as e:
        print(f"[email alert failed: {e}]")


def check_micro1():
    """
    Searches Micro1 specifically for open roles, checks the results against
    the user's skill list, and compares against the last check to flag
    whether anything actually changed since last time.
    """
    queries = [
        "Micro1 open roles hiring now 2026",
        "Micro1 careers apply annotator evaluator",
        "Micro1 AI interview jobs requirements"
    ]

    combined = ""
    for q in queries:
        print(f"[checking Micro1: {q}]")
        combined += web_search(q, max_results=3) + "\n"

    # Check which of the user's skills appear anywhere in the results
    lower_combined = combined.lower()
    matched_skills = [s for s in MY_SKILLS if s.lower() in lower_combined]

    # Compare against last check to see if anything actually changed
    log = load_micro1_log()
    current_hash = hash_text(combined)
    is_new_check = log["last_hash"] is None
    has_changed = log["last_hash"] != current_hash

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    report = f"MICRO1 CHECK — {now}\n\n"

    if matched_skills:
        report += (
            f"*** ALERT: possible skill match found ***\n"
            f"Matched: {', '.join(matched_skills)}\n"
            f"Recommend reviewing and applying quickly if this is a real open role.\n\n"
        )
        send_email_alert(
            subject="Micro1 alert: possible skill match found",
            body=(
                f"Micro1 check on {now} found a possible match.\n\n"
                f"Matched skills: {', '.join(matched_skills)}\n\n"
                f"Raw results:\n{combined}"
            )
        )
    else:
        report += "No skill matches found in this check.\n\n"

    if is_new_check:
        report += "This is the first time Micro1 has been checked, no history to compare against yet.\n\n"
    elif has_changed:
        report += "Results have changed since the last check.\n\n"
    else:
        report += f"No change since last check on {log['last_checked']}.\n\n"

    report += f"Raw search results:\n{combined}"

    # Save this check for next time
    save_micro1_log({
        "last_checked": now,
        "last_hash": current_hash,
        "last_result": combined
    })

    return report


tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information on a general topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_micro1",
            "description": (
                "Checks Micro1 specifically for open roles, compares against the user's skill list, "
                "and flags a clear alert if any open roles seem to match. Also reports whether "
                "anything has changed since the last check. Use this whenever the user asks about "
                "Micro1, wants to know if there are new opportunities there, or wants a skill match check."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        f"You are a helpful agent focused on tracking opportunities on Micro1 for the user. "
        f"The user's skills are: {', '.join(MY_SKILLS)}. Use check_micro1 whenever the user asks "
        f"about Micro1, new roles, or skill matches there. If the tool result contains an ALERT, "
        f"put that at the very top of your reply in clear, direct language, and tell the user to "
        f"apply soon. Use web_search only for things unrelated to Micro1. Do not call the same tool "
        f"more than twice in a row. You have memory of past conversations, check earlier messages "
        f"before saying you don't know something about the user."
    )
}


def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return [SYSTEM_PROMPT]


def save_memory(messages):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2)


messages = load_memory()


def run_agent_turn(user_input):
    messages.append({"role": "user", "content": user_input})

    while True:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        assistant_msg = {
            "role": "assistant",
            "content": message.content
        }
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments
                    }
                } for call in message.tool_calls
            ]
        messages.append(assistant_msg)

        if message.tool_calls:
            for call in message.tool_calls:
                args = json.loads(call.function.arguments) if call.function.arguments else {}

                if call.function.name == "web_search":
                    print(f"[searching: {args.get('query')}]")
                    result = web_search(args["query"])
                elif call.function.name == "check_micro1":
                    result = check_micro1()
                else:
                    result = "Unknown tool."

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result
                })
        else:
            save_memory(messages)
            return message.content


if __name__ == "__main__":
    print("Agent ready. Tracking Micro1 for skill matches. Type your question, or 'quit' to exit.\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break
        answer = run_agent_turn(user_input)
        print(f"\nAgent: {answer}\n")
