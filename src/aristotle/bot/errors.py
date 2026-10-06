from __future__ import annotations

import html
import logging
import traceback

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

log = logging.getLogger(__name__)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log dell'errore + notifica all'admin (equivalente del DM all'owner di Socrates)."""
    err = context.error
    log.error("Unhandled exception", exc_info=err)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("Errore interno. L'admin e' stato avvisato.")
        except Exception:
            log.debug("Impossibile avvisare l'utente", exc_info=True)

    admin_id = context.application.bot_data["settings"].admin_chat_id
    if admin_id and err:
        tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))[-3500:]
        try:
            await context.bot.send_message(
                admin_id, f"<pre>{html.escape(tb)}</pre>", parse_mode=ParseMode.HTML
            )
        except Exception:
            log.exception("Impossibile notificare l'admin")
