import json

import httpx
import pytest

from aristotle.bot.formatters import (
    POWERED_BY,
    format_combat_orders,
    format_epics,
    format_mpp,
    format_sh,
    mpps_csv,
    paginate,
)
from aristotle.core.battles import (
    BattleService,
    parse_campaigns,
    select_combat_orders,
    select_epics,
    select_sh,
)
from aristotle.core.client import ErepApiError
from aristotle.core.countries import load_countries
from aristotle.core.mpp import MppService, parse_map
from aristotle.core.site import ErepSiteClient, SiteBlocked

NOW = 1_000_000


def div(number, *, epic=0, epic_type=0, end=False, inv=None, dfn=None, co_inv=(), co_def=(),
        wall_for=10, dom=60.0):
    return {
        "div": number, "epic": epic, "epic_type": epic_type, "division_end": end,
        "stats": {"inv": {"damage": inv} if inv is not None else None,
                  "def": {"damage": dfn} if dfn is not None else None},
        "co": {"inv": list(co_inv), "def": list(co_def)},
        "wall": {"for": wall_for, "dom": dom},
    }


def battle(bid, btype, start, divs, inv=10, dfn=12, region="Veneto"):
    return {"id": bid, "type": btype, "start": start, "inv": {"id": inv}, "def": {"id": dfn},
            "region": {"name": region}, "div": divs}


def campaigns(battles):
    return json.dumps({"time": NOW, "battles": {str(b["id"]): b for b in battles}})


CO = {"co_id": "c1", "reward": "5", "budget": "1000", "threshold": "40"}

PAYLOAD = campaigns([
    battle(1, "aircraft", NOW + 125, {"1": div(11)}),                       # in arrivo
    battle(2, "aircraft", NOW - 70, {"2": div(11, inv=100, dfn=50000)}),    # danno basso
    battle(3, "aircraft", NOW - 70, {"3": div(11, inv=40000, dfn=50000)}),  # danno alto: escluso
    battle(4, "tanks", NOW - 10, {"4": div(1, epic=2, epic_type=5), "5": div(2, epic=1)}),
    battle(5, "tanks", NOW - 10, {"6": div(1, epic=2, end=True)}),          # epic gia' finita
    battle(6, "tanks", NOW - 10, {"7": div(1, co_inv=[CO], wall_for=10, dom=60.0),
                                  "8": div(2, co_inv=[CO, {**CO, "co_id": "c2"}],
                                           co_def=[CO], wall_for=12, dom=70.0)}),
])


def test_parse_and_sh():
    rows = select_sh(parse_campaigns(PAYLOAD))
    assert [r.battle.id for r in rows] == [1, 2]
    assert rows[0].upcoming and rows[0].delay == 125
    assert not rows[1].upcoming and rows[1].started_since == 70 and rows[1].inv_damage == 100


def test_epics():
    rows = select_epics(parse_campaigns(PAYLOAD))
    got = {(r.battle.id, r.division, r.kind) for r in rows}
    # battle 5 ha solo una epic terminata: nessuna delle sue divisioni deve comparire
    assert got == {(4, 1, "Most Contested"), (4, 2, "Fullscale")}
    assert all(r.started_since == 10 for r in rows)


def test_combat_orders_dedup_and_wall():
    rows = select_combat_orders(parse_campaigns(PAYLOAD))
    inv = [r for r in rows if r.side_country_id == 10]
    dfn = [r for r in rows if r.side_country_id == 12]
    assert [r.order.co_id for r in inv] == ["c1", "c2"]  # c1 non duplicato tra le due div
    assert inv[0].wall == 60.0
    assert dfn[0].wall == 70.0  # wall_for == lato difensore (12)
    assert inv[1].wall == pytest.approx(30.0)  # div 8: wall e' per 12, quindi 100 - 70


def test_parse_rejects_garbage():
    for bad in ("not json", "{}", json.dumps({"time": 1, "battles": {"1": {}}})):
        with pytest.raises(ErepApiError):
            parse_campaigns(bad)


def test_formatters_have_footer_and_links():
    cs = load_countries()
    c = parse_campaigns(PAYLOAD)
    for pages in (
        format_sh(select_sh(c), cs),
        format_epics(select_epics(c), cs),
        format_combat_orders(select_combat_orders(c), cs),
    ):
        assert pages[-1].endswith(POWERED_BY)
    assert "battlefield/1" in format_sh(select_sh(c), cs)[0]
    assert "battlefield/6/7" in format_combat_orders(select_combat_orders(c), cs)[0]
    for empty in (format_sh([], cs), format_epics([], cs), format_combat_orders([], cs)):
        assert len(empty) == 1 and empty[0].endswith(POWERED_BY)


def test_paginate_splits_and_footer_only_last():
    lines = ["x" * 500] * 20
    pages = paginate("<b>T</b>", lines)
    assert len(pages) > 1 and all(len(p) < 4096 for p in pages)
    assert pages[-1].endswith(POWERED_BY)
    assert not any(POWERED_BY in p for p in pages[:-1])


MAP_XML = """<?xml version="1.0"?>
<response><countries>
<country c_id="10" name="Italy"><mpps><mpp c_id="12" expires="20261103"/><mpp c_id="11" expires="20260901"/></mpps></country>
<country c_id="12" name="Germany"><mpps> </mpps></country>
</countries></response>"""


def test_parse_map_sorted_and_empty():
    m = parse_map(MAP_XML)
    assert [x.partner_id for x in m[10]] == [11, 12]  # ordinati per scadenza
    assert m[12] == []
    with pytest.raises(ErepApiError):
        parse_map("<broken")


def test_mpp_format_and_csv():
    cs = load_countries()
    m = parse_map(MAP_XML)
    text = format_mpp("Italy", m[10], cs)[0]
    assert "2026-09-01" in text and text.endswith(POWERED_BY)
    assert "Nessun MPP" in format_mpp("Germany", [], cs)[0]
    csv_text = mpps_csv(m, cs)
    assert csv_text.splitlines()[0] == "Italy;France;01/09/2026"
    assert len(csv_text.splitlines()) == 2


def make_site(handler):
    return ErepSiteClient(http=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


async def test_site_blocked_on_challenge():
    site = make_site(lambda r: httpx.Response(
        403, headers={"cf-mitigated": "challenge"}, text="<title>Just a moment...</title>"))
    with pytest.raises(SiteBlocked):
        await BattleService(site).sh()


async def test_site_other_errors_and_cache():
    calls = []

    def handler(request):
        calls.append(request.url.host)
        return httpx.Response(200, text=PAYLOAD)

    site = make_site(handler)
    svc = BattleService(site)
    await svc.sh()
    await svc.epics()
    assert calls == ["www.erepublik.com"]  # seconda chiamata dalla cache

    with pytest.raises(ErepApiError) as exc:
        await BattleService(make_site(lambda r: httpx.Response(500))).sh()
    assert not isinstance(exc.value, SiteBlocked)


async def test_mpp_service():
    svc = MppService(make_site(lambda r: httpx.Response(200, text=MAP_XML)))
    assert len(await svc.for_country(10)) == 2
    assert await svc.for_country(999) == []
