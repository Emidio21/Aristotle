from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ...core.erepday import DayToDate, InvalidDateInput, convert

CONVERT_USAGE = "Uso: /convert <eRepublik day> oppure /convert <gg/mm/aaaa>, es. /convert 5000"


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("Pong")


async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    text = " ".join(context.args or [])
    if not text.strip():
        await msg.reply_text(CONVERT_USAGE)
        return
    try:
        result = convert(text)
    except InvalidDateInput:
        await msg.reply_text("Input non valido. " + CONVERT_USAGE)
        return

    if isinstance(result, DayToDate):
        out = f"eRepublik day <b>{result.erep_day}</b> = <b>{result.date:%d/%m/%Y}</b>"
    else:
        out = f"<b>{result.date:%d/%m/%Y}</b> = eRepublik day <b>{result.erep_day}</b>"
    await msg.reply_text(out, parse_mode=ParseMode.HTML)
