from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

# eRepublik day 1 (come in Socrates, meta.py).
EPOCH = date(2007, 11, 21)


class InvalidDateInput(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DayToDate:
    erep_day: int
    date: date


@dataclass(frozen=True, slots=True)
class DateToDay:
    date: date
    erep_day: int


def day_to_date(erep_day: int) -> date:
    if erep_day < 1:
        raise InvalidDateInput(str(erep_day))
    try:
        return EPOCH + timedelta(days=erep_day - 1)
    except OverflowError:
        raise InvalidDateInput(str(erep_day)) from None


def date_to_day(d: date) -> int:
    day = (d - EPOCH).days + 1
    if day < 1:
        raise InvalidDateInput(d.isoformat())
    return day


def convert(text: str) -> DayToDate | DateToDay:
    """'1234' -> data di quell'eRepublik day; 'dd/mm/yyyy' -> numero del giorno."""
    text = text.strip()
    if text.isdigit():
        n = int(text)
        return DayToDate(n, day_to_date(n))
    try:
        d = datetime.strptime(text, "%d/%m/%Y").date()  # noqa: DTZ007 - solo data, niente fuso
    except ValueError:
        raise InvalidDateInput(text) from None
    return DateToDay(d, date_to_day(d))
