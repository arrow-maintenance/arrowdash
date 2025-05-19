import mailbox
from email.utils import parsedate_to_datetime, timezone
from collections import defaultdict
from datetime import datetime, timezone 
import re
from email.header import decode_header, make_header

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
  
  
th2 = read_mbox_as_threads("dev_ml.mbox")

th2[6]["thread"]

# 1. get messages as threads
# 2. for each thread, summarise the participants, the topic, and overall what was said in the dicussion
# 3. combine each summary and summarise themes
