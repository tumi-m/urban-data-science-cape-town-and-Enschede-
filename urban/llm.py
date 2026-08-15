"""A grounded section assistant, served by Ollama Cloud.

The whole report is built to stop a reader carrying a number out of the room
that did not earn its way in. An LLM is the most efficient machine ever built
for producing confident-sounding output from weak inputs, so it is used here in
exactly one way: as a reader's interpreter of what is already on the page, not
as a new source.

The discipline is mechanical rather than editorial:

  - The only context the model sees is the current section's own computed
    numbers and prose, gathered into one block. It is told those are the whole
    universe of admissible facts.
  - The system prompt forbids inventing figures, forbids drawing on prior
    knowledge about the cities, and instructs it to say it does not have
    something on this page when the question is not answerable from the
    context. That last clause is the one that keeps it honest: a refusal is a
    better answer than a plausible hallucination, and the model is told so.
  - The box is labelled AI, and degrades to nothing when no API key is set —
    so a deployment without a key loses a convenience and gains nothing false.

The call is stdlib HTTP to https://ollama.com/api/chat with a Bearer key, so no
new dependency is added to a stack that is deliberately lean for Streamlit
Cloud. The key is read from Streamlit secrets (``ollama_api_key``) with an
``OLLAMA_API_KEY`` environment-variable fallback, and never from the repo.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

import streamlit as st

# The capable, moderately fast cloud model. Overridable from secrets so a
# deployment can pick a lighter or heavier model without touching code.
DEFAULT_MODEL = "deepseek-v4-flash:0731"
CLOUD_CHAT_URL = "https://ollama.com/api/chat"
REQUEST_TIMEOUT = 60


# The system prompt is the load-bearing part of this module. Everything that
# keeps the assistant from manufacturing credibility is stated here, and the
# user's question plus the section context are appended as the only admissible
# facts. If this prompt is softened, the guardrail is gone.
SYSTEM_PROMPT = """You are the reader's interpreter for one section of an urban
data-science report comparing Cape Town and Enschede. The reader can see the
section; your job is to help them read it.

You operate under one absolute rule: the CONTEXT block below is the entire
universe of facts you may draw on. Everything the report concludes is in it,
worked out from the report's own numbers.

- Answer only from the CONTEXT block. Do not bring in any prior knowledge about
  Cape Town, Enschede, the Netherlands, South Africa, nitrogen policy, or any
  other subject. If a fact is not in the CONTEXT block, it is not available to
  you.
- Never invent a number. If a figure the reader asks about is not in the
  context, say plainly that this page does not state it, and point at the
  closest number that is. Do not estimate, round, or fill gaps.
- Keep every number you quote identical to how it appears in the context,
  including its unit and its provenance class (official / derived / engineering
  / estimate / reconstructed / synthetic) where one is given.
- Be brief and direct. Plain language, short paragraphs, no bullet points
  unless the reader asked for a list. Match the report's tone: factual,
  understated, willing to say what the analysis does not know.
- If the question is not answerable from the context, say so in one sentence
  and stop. A clear "this page does not cover that" is the correct answer, not
  a failure.

You are labelled as AI wherever you appear. You are not a source."""


def _api_key() -> str | None:
    """The Ollama key, from Streamlit secrets then the environment.

    Read fresh on each call rather than at import time, so a key added to the
    Cloud dashboard mid-session is picked up without a restart.
    """
    try:
        secret = st.secrets.get("ollama_api_key")
        if secret:
            return str(secret)
    except Exception:
        # st.secrets raises if no secrets file exists at all — that is the
        # normal "no key configured" state, not an error to surface.
        pass
    return os.environ.get("OLLAMA_API_KEY")


def _model() -> str:
    try:
        m = st.secrets.get("ollama_model")
        if m:
            return str(m)
    except Exception:
        pass
    return os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL)


def is_configured() -> bool:
    """Whether a key is present. The UI hides itself entirely when this is False."""
    return bool(_api_key())


def _chat(messages: list[dict], *, temperature: float = 0.2) -> dict[str, Any]:
    """One non-streaming call to Ollama Cloud. Raises on network/HTTP error.

    Low temperature because the task is restating the context, not being
    creative: the model should be as deterministic as a summary can be.
    """
    key = _api_key()
    if not key:
        raise RuntimeError("No Ollama API key configured.")
    payload = json.dumps({
        "model": _model(),
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }).encode("utf-8")
    req = urllib.request.Request(
        CLOUD_CHAT_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:  # noqa: S310 — fixed HTTPS URL
        return json.loads(resp.read().decode("utf-8"))


def answer(context: str, question: str) -> str:
    """Answer `question` using only `context`.

    `context` is the section's computed numbers and prose, assembled by the
    caller. The system prompt plus that block plus the question is the whole
    prompt; there is no history, so each question is answered from the section
    alone and the model cannot drift across turns.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {question}"},
    ]
    data = _chat(messages)
    return str(data.get("message", {}).get("content", "")).strip()


def assistant_box(context: str, *, key: str = "llm_assistant",
                  label: str = "Ask this section") -> None:
    """A labelled, grounded Q&A box for one section.

    Renders nothing when no key is configured, so a deployment without one
    loses the feature and gains nothing misleading. When configured, it shows
    an expander containing the question input, the answer, the AI label, the
    grounding note, and the model name — everything a reader needs to know what
    they are looking at.
    """
    if not is_configured():
        return

    with st.expander(f"💬 {label}", expanded=False):
        st.caption(
            "AI assistant · answers only from the numbers and text on this "
            "page. It cannot see other sections or invent figures; if the page "
            "does not state something, it will say so.")
        question = st.text_input(
            "Ask a question about this section",
            placeholder="e.g. Why is Enschede's permitted land zero?",
            key=f"{key}_q", label_visibility="collapsed")

        if not question:
            st.caption("Type a question above and press Enter.")
            return

        try:
            with st.spinner("Reading the page…"):
                reply = answer(context, question)
        except Exception as exc:
            st.caption(f"The assistant could not respond right now "
                       f"({type(exc).__name__}).")
            return

        st.markdown(reply)
        st.caption(
            f"AI-generated, grounded in this page only · model: {_model()}. "
            "Treat it as a reading aid, not a source.")