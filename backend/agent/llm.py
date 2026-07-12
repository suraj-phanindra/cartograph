"""Thin Anthropic client for the agent's reasoning stages (Reader/Skeptic/Reviewer).

Uses httpx directly (no extra SDK). If ANTHROPIC_API_KEY is unset the agent degrades
honestly — the deterministic backbone (resolve/retrieve/verify/emit) and every
anti-fabrication guarantee still work; the reasoning stages simply return their
honest "not configured" outcome. The model is never the source of truth: the Stage 4
verify gate re-checks every citation regardless of what the model says.
"""
from __future__ import annotations

import json
import re

import httpx

from backend import config

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def available():
    return bool(config.ANTHROPIC_API_KEY)


def call(system, user, max_tokens=3000, timeout=90):
    if not available():
        raise RuntimeError("ANTHROPIC_API_KEY not configured")
    headers = {"x-api-key": config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01",
               "content-type": "application/json"}
    body = {"model": config.ANTHROPIC_MODEL, "max_tokens": max_tokens,
            "system": system, "messages": [{"role": "user", "content": user}]}
    r = httpx.post(ANTHROPIC_URL, headers=headers, json=body, timeout=timeout)
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")


def call_json(system, user, **kw):
    """Call and parse the first JSON value in the reply, or None. Tolerates markdown
    fences and surrounding prose; a truncated/invalid reply returns None (an honest
    failure -> topology-only), never a fabricated dossier."""
    txt = call(system, user, **kw).strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```[a-zA-Z]*\s*", "", txt)
        txt = re.sub(r"\s*```$", "", txt).strip()
    m = re.search(r"(\{.*\}|\[.*\])", txt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
