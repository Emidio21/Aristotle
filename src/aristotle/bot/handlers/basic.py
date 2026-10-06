from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

HELP_TEXT = (
    "<b>Aristotle</b> - eRepublik bot\n\n"
    "/user &lt;id o nome&gt; - scheda cittadino\n"
    "/food, /weapons, /tickets, /houses, /aircrafts &lt;qualita 1-7&gt; - migliori offerte\n"
    "/frm, /wrm, /hrm, /arm - migliori offerte raw material\n"
    "/jobs [paese] - migliori offerte di lavoro\n"
    "/rh &lt;paese&gt; - regioni occupate\n"
    "/sh - round aerei in arrivo o a basso danno\n"
    "/epic - battaglie epic e full-scale\n"
    "/co - combat order attivi\n"
    "/mpp &lt;paese&gt; - MPP di un paese\n"
    "/mppsraw - CSV di tutti gli MPP\n"
    "/convert &lt;eRep day | gg/mm/aaaa&gt; - converte giorno eRepublik e data\n"
    "/ping - verifica che il bot risponda\n"
    "/help - questo messaggio"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)
