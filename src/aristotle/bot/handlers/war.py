from __future__ import annotations

import io
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from ...core.client import ErepApiError
from ...core.countries import load_countries
from ...core.site import SiteBlocked
from ..formatters import (
    format_combat_orders,
    format_epics,
    format_mpp,
    format_sh,
    mpps_csv,
)
from .common import BLOCKED, UNAVAILABLE, resolve_country, send_pages


async def _fail(update: Update, exc: ErepApiError) -> None:
    await update.effective_message.reply_text(BLOCKED if isinstance(exc, SiteBlocked) else UNAVAILABLE)


def _data(context: ContextTypes.DEFAULT_TYPE, key: str):
    return context.application.bot_data[key]


async def sh_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        rows = await _data(context, "battle_service").sh()
    except ErepApiError as exc:
        await _fail(update, exc)
        return
    await send_pages(update.effective_message, format_sh(rows, load_countries()))


async def epic_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        rows = await _data(context, "battle_service").epics()
    except ErepApiError as exc:
        await _fail(update, exc)
        return
    await send_pages(update.effective_message, format_epics(rows, load_countries()))


async def co_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        rows = await _data(context, "battle_service").combat_orders()
    except ErepApiError as exc:
        await _fail(update, exc)
        return
    await send_pages(update.effective_message, format_combat_orders(rows, load_countries()))


async def mpp_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    query = " ".join(context.args or []).strip()
    if not query:
        await msg.reply_text("Uso: /mpp <paese>, es. /mpp italy")
        return
    country = await resolve_country(msg, query)
    if country is None:
        return
    try:
        mpps = await _data(context, "mpp_service").for_country(country.id)
    except ErepApiError as exc:
        await _fail(update, exc)
        return
    await send_pages(msg, format_mpp(country.name, mpps, load_countries()))


async def mppsraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    try:
        everything = await _data(context, "mpp_service").all()
    except ErepApiError as exc:
        await _fail(update, exc)
        return
    csv_text = mpps_csv(everything, load_countries())
    name = f"mpps{datetime.now().strftime('%d-%m-%Y')}.csv"  # noqa: DTZ005
    await msg.reply_document(io.BytesIO(csv_text.encode("utf-8")), filename=name)
