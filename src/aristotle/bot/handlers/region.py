from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ...core.client import ErepApiError
from ...core.countries import load_countries
from ..formatters import format_rh
from .common import UNAVAILABLE, resolve_country


async def rh_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    query = " ".join(context.args or []).strip()
    if not query:
        await msg.reply_text("Uso: /rh <paese>, es. /rh italy")
        return
    country = await resolve_country(msg, query)
    if country is None:
        return

    try:
        result = await context.application.bot_data["region_service"].occupied_for(country.id)
    except ErepApiError:
        await msg.reply_text(UNAVAILABLE)
        return

    await msg.reply_text(
        format_rh(country.name, result, load_countries()),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
