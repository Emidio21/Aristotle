from __future__ import annotations

from telegram import Message
from telegram.constants import ParseMode

from ...core.countries import Country, load_countries

UNAVAILABLE = "Il servizio dati eRepublik non risponde al momento. Riprova piu' tardi."


async def resolve_country(msg: Message, query: str) -> Country | None:
    """Risolve un nome paese; se non univoco risponde all'utente e ritorna None."""
    found = load_countries().find(query)
    if not found:
        await msg.reply_text(f"Paese '{query}' non trovato.")
        return None
    if len(found) > 1:
        names = ", ".join(c.name for c in found[:8])
        more = "..." if len(found) > 8 else ""
        await msg.reply_text(f"'{query}' e' ambiguo: {names}{more}. Specifica meglio.")
        return None
    return found[0]


BLOCKED = (
    "erepublik.com sta bloccando le richieste automatiche del bot (protezione anti-bot). "
    "Riprova piu' tardi."
)


async def send_pages(msg: Message, pages: list[str]) -> None:
    for page in pages:
        await msg.reply_text(page, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
