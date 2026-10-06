from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ...core.client import ErepApiError, InvalidRequest
from ...core.countries import load_countries
from ...core.market import InvalidQuality, MarketItem, parse_quality
from ..formatters import format_jobs, format_offers
from .common import UNAVAILABLE, resolve_country


def make_market_handler(item: MarketItem):
    """Crea l'handler di un comando di mercato (es. /food 1, /frm)."""

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.effective_message
        if item.fixed_quality is not None:
            quality = item.fixed_quality
        else:
            try:
                quality = parse_quality(" ".join(context.args or []))
            except InvalidQuality:
                await msg.reply_text(f"Uso: /{item.command} <qualita 1-7>, es. /{item.command} 1")
                return

        try:
            offers = await context.application.bot_data["market_service"].best_offers(
                item, quality
            )
        except InvalidRequest:
            await msg.reply_text(f"Qualita {quality} non valida per {item.title}.")
            return
        except ErepApiError:
            await msg.reply_text(UNAVAILABLE)
            return

        title = item.title if item.fixed_quality else f"{item.title} Q{quality}"
        await msg.reply_text(
            format_offers(title, offers, load_countries()),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    handler.__name__ = f"market_{item.command}"
    return handler


async def jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    query = " ".join(context.args or []).strip()
    country_id = None
    title = "Migliori offerte di lavoro"
    if query:
        found = await resolve_country(msg, query)
        if found is None:
            return
        country_id = found.id
        title += f" - {found.name}"

    try:
        offers = await context.application.bot_data["market_service"].job_offers(country_id)
    except ErepApiError:
        await msg.reply_text(UNAVAILABLE)
        return

    await msg.reply_text(
        format_jobs(title, offers, load_countries()),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
