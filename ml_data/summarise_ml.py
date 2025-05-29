import mailbox
from email.utils import parsedate_to_datetime
from collections import defaultdict
from datetime import datetime, timezone 
import re
from email.header import decode_header, make_header
import os
from chatlas import ChatGoogle
import ml_data.data_methods as ml

def decode_mime_words(s):
    if s is None:
        return None
    try:
        return str(make_header(decode_header(s)))
    except Exception:
        return s  # fallback to raw if decoding fails

def strip_quoted_reply(text):
    # Remove anything that starts with typical reply indicators
    patterns = [
        r"\n\s*>",                          # quoted lines
        r"\nOn .*wrote:",                   # "On [date], X wrote:"
        r"\nFrom: .*",                      # "From: X" line in forwarded messages
    ]
    for pattern in patterns:
        split = re.split(pattern, text, maxsplit=1, flags=re.IGNORECASE)
        if len(split) > 1:
            return split[0].strip()
    return text.strip()
  
def extract_message_info(message):
    if message.is_multipart():
        parts = []
        for part in message.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                payload = part.get_payload(decode=True)
                if payload:
                    parts.append(payload.decode(errors='replace'))
        contents = "\n".join(parts)
    else:
        payload = message.get_payload(decode=True)
        contents = payload.decode(errors='replace') if payload else ""

    return {
        "author": decode_mime_words(message.get("from")),
        "datetime": safe_parse_date(message.get("date")),
        "contents": strip_quoted_reply(contents)
    }

def safe_parse_date(date_str):
    try:
        dt = parsedate_to_datetime(date_str)
        if dt is None:
            return None
        if dt.tzinfo is None:
            # Make it timezone-aware in UTC
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None
def get_thread_root_id(message):
    # Find earliest reference if present; else fallback to In-Reply-To; else its own ID
    references = message.get('References')
    if references:
        return references.split()[0]  # first in chain = root
    in_reply_to = message.get('In-Reply-To')
    if in_reply_to:
        return in_reply_to
    return message.get('Message-ID')

def read_mbox_as_threads(mbox_file):
    mbox = mailbox.mbox(mbox_file)
    threads = defaultdict(list)

    for key, message in mbox.items():
        root_id = get_thread_root_id(message)
        threads[root_id].append(message)

    thread_list = []
    for thread_id, messages in threads.items():
        messages.sort(key=lambda m: safe_parse_date(m.get("date")) or datetime.min.replace(tzinfo=timezone.utc))
        first_message = messages[0]
        
        message_dicts = [extract_message_info(m) for m in messages]
        participants = sorted({m["author"] for m in message_dicts if m["author"]})

        thread_list.append({
            "key": thread_id,
            "subject": first_message.get("subject"),
            "participants": participants,
            "thread": message_dicts
        })

    return thread_list
  
def fmt_msg(msg):
    dt = msg['datetime'].strftime('%Y-%m-%d %H:%M')
    return f"{msg['author']} on {dt}:\n{msg['contents'].strip()}\n"


def thread_to_string(thread):
    return "\n".join(fmt_msg(msg) for msg in thread)


def message_dict_to_string(msg_dict):
    subject = msg_dict['subject']
    participants = ", ".join(msg_dict['participants'])
    thread_str = thread_to_string(msg_dict['thread'])
    return f"Subject: {subject}\nParticipants: {participants}\n\nThread:\n{thread_str}"

def summarisation_input(threads: list[dict]) -> str:
    return "\n" + "\n\n" + "-" * 80 + "\n\n".join(
        message_dict_to_string(thread) for thread in threads
    )
    
def summarise_dev_ml():
  ml.get_messages("dev")

  th2 = read_mbox_as_threads("dev_ml.mbox")
  thread_string = summarisation_input(th2)
  chat = ChatGoogle(api_key=os.getenv("GOOGLE_API_KEY"))

  with open("./ml_data/prompt_ml_summary.txt", "r", encoding="utf-8") as f:
    chat_prompt = f.read()

  summary = chat.chat(chat_prompt, thread_string, echo = "none")
  return str(summary)


