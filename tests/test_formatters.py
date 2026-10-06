from aristotle.bot.formatters import format_citizen
from aristotle.core.models import Citizen


def test_html_is_escaped():
    text = format_citizen(Citizen(id=1, name="<b>evil</b> & co", mu_id=5, mu_name="MU <x>"))
    assert "<b>evil</b>" not in text
    assert "&lt;b&gt;evil&lt;/b&gt; &amp; co" in text
    assert "MU &lt;x&gt;" in text


def test_optional_fields_skipped():
    text = format_citizen(Citizen(id=1, name="Plato"))
    assert "Party" not in text and "Newspaper" not in text and "Military Unit" not in text
    assert "<b>Status:</b> Alive" in text


def test_dead_status():
    assert "Dead" in format_citizen(Citizen(id=1, name="x", is_alive=False))


def test_rank_names_from_socrates():
    from aristotle.core.data.ranks import RANKS_AIR, RANKS_GROUND, air_rank, ground_rank

    assert (len(RANKS_GROUND), len(RANKS_AIR)) == (89, 61)
    assert ground_rank(1) == "Recruit" and ground_rank(89) == "Legend XX"
    assert air_rank(1) == "Airman" and air_rank(61) == "Air Commodore *****"
    assert ground_rank(90) == "Rank 90" and ground_rank(0) is None and air_rank(None) is None
