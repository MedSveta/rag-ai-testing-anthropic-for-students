from __future__ import annotations

from xml.sax.saxutils import escape

from app.vector_store import RetrievedContext

MISSING_INFORMATION_ANSWER = "The information is not specified in the knowledge base."

SYSTEM_PROMPT = f"""You are a requirements assistant for the PhoneBook training project.
Answer ONLY from the context provided by the RAG system.

Rules:
1. Never invent a product requirement.
2. If the context does not contain enough information, answer exactly:
   \"{MISSING_INFORMATION_ANSWER}\"
3. When a supporting requirement ID such as T14 or F8 is present, cite it in square brackets.
4. If the source itself is ambiguous or contradictory, state that clearly instead of silently resolving it.
5. Keep the answer concise and factual.
"""


def build_user_prompt(question: str, contexts: list[RetrievedContext]) -> str:
    blocks = []
    for index, context in enumerate(contexts, start=1):
        ids = ", ".join(context.requirement_ids) or "none"
        blocks.append(
            f'<document index="{index}" source="{escape(context.source)}" '
            f'section="{escape(context.section)}" requirement_ids="{escape(ids)}">\n'
            f"{escape(context.text)}\n</document>"
        )
    context_xml = "\n\n".join(blocks)
    return (
        "<context>\n"
        f"{context_xml}\n"
        "</context>\n\n"
        "<question>\n"
        f"{escape(question.strip())}\n"
        "</question>"
    )
