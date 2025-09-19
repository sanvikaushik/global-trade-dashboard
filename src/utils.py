from __future__ import annotations
import re
import hashlib

def slug(text: str) -> str:
    s = re.sub(r'\s+', ' ', text or '').strip().lower()
    s = re.sub(r'[^a-z0-9\- ]', '', s)
    return s.replace(' ', '-')

def stable_id(*parts: str, prefix: str = "") -> str:
    m = hashlib.sha1()
    for p in parts:
        m.update((p or "").encode("utf-8"))
        m.update(b"|")
    return f"{prefix}{m.hexdigest()[:12]}"
