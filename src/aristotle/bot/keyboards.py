from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..core.models import CitizenSummary

USER_PICK_PREFIX = "user:"


def citizen_choices(candidates: list[CitizenSummary]) -> InlineKeyboardMarkup:
    """Un bottone per omonimo. callback_data contiene solo l'ID (limite 64 byte)."""
    rows = [
        [InlineKeyboardButton(f"{c.name} ({c.id})", callback_data=f"{USER_PICK_PREFIX}{c.id}")]
        for c in candidates
    ]
    return InlineKeyboardMarkup(rows)
