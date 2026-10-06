from __future__ import annotations

import logging

from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from ...core.client import CitizenNotFound, ErepApiError
from ...core.services import Ambiguous, CitizenService, NoMatch, Resolved, TooMany
from ..formatters import avatar_url, format_citizen
from ..keyboards import USER_PICK_PREFIX, citizen_choices

log = logging.getLogger(__name__)

UNAVAILABLE = "Il servizio dati eRepublik non risponde al momento. Riprova piu' tardi."


def _service(context: ContextTypes.DEFAULT_TYPE) -> CitizenService:
    return context.application.bot_data["citizen_service"]


async def _send_card(bot: Bot, chat_id: int, citizen) -> None:
    text = format_citizen(citizen)
    try:
        await bot.send_photo(
            chat_id, avatar_url(citizen.id), caption=text, parse_mode=ParseMode.HTML
        )
    except BadRequest:
        # Avatar non raggiungibile da Telegram: ripiega sul solo testo.
        await bot.send_message(
            chat_id, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )


async def user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    query = " ".join(context.args or []).strip()
    if not query:
        await msg.reply_text("Uso: /user <id o nome>")
        return

    try:
        result = await _service(context).resolve(query)
    except CitizenNotFound:
        await msg.reply_text("Cittadino non trovato.")
        return
    except ErepApiError:
        await msg.reply_text(UNAVAILABLE)
        return

    match result:
        case Resolved(citizen):
            await _send_card(context.bot, msg.chat_id, citizen)
        case Ambiguous(candidates):
            await msg.reply_text(
                "Piu' cittadini corrispondono, scegli:", reply_markup=citizen_choices(candidates)
            )
        case TooMany(total):
            await msg.reply_text(
                f"'{query}' ha troppi risultati ({total}). Specifica meglio il nome."
            )
        case NoMatch():
            await msg.reply_text(f"'{query}' non corrisponde a nessun cittadino.")


async def user_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    try:
        citizen_id = int(q.data.removeprefix(USER_PICK_PREFIX))
        citizen = await _service(context).get(citizen_id)
    except (ValueError, CitizenNotFound):
        await q.edit_message_text("Cittadino non trovato.")
        return
    except ErepApiError:
        await q.edit_message_text(UNAVAILABLE)
        return

    await q.edit_message_reply_markup(reply_markup=None)
    await _send_card(context.bot, q.message.chat_id, citizen)
