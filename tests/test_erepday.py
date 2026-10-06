from datetime import date

import pytest

from aristotle.core.erepday import DateToDay, DayToDate, InvalidDateInput, convert


def test_day_one_is_epoch():
    assert convert("1") == DayToDate(1, date(2007, 11, 21))
    assert convert("21/11/2007") == DateToDay(date(2007, 11, 21), 1)


def test_roundtrip():
    r = convert("5000")
    assert convert(r.date.strftime("%d/%m/%Y")).erep_day == 5000


def test_whitespace_ok():
    assert convert("  2 ").date == date(2007, 11, 22)


@pytest.mark.parametrize(
    "bad", ["", "abc", "0", "20/11/2007", "31/02/2020", "2020-01-01", "99999999999999"]
)
def test_invalid(bad):
    with pytest.raises(InvalidDateInput):
        convert(bad)
