import httpx

from aristotle.bot.formatters import format_rh
from aristotle.core.client import ErepToolsClient
from aristotle.core.countries import load_countries
from aristotle.core.regions import MAX_REGIONS, RegionService


def region(i, orig, cur, since):
    return {
        "id": i,
        "name": f"R{i}",
        "original_owner_country_id": orig,
        "current_owner_country_id": cur,
        "under_occupation_since": {"date": since + ".000000"} if since else None,
    }


def service(regions):
    http = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"regions": regions}))
    )
    return RegionService(ErepToolsClient(api_key="K", http=http))


async def test_filters_sorts_and_includes_occupier():
    regions = [
        region(1, 10, 10, None),  # non occupata
        region(2, 10, 11, "2020-01-01 00:00:00"),  # Italy occupata da altri
        region(3, 12, 10, "2022-01-01 00:00:00"),  # Italy occupa
        region(4, 12, 13, "2023-01-01 00:00:00"),  # estranea
    ]
    res = await service(regions).occupied_for(10)
    assert [r.id for r in res.shown] == [3, 2]  # piu' recente prima
    assert res.total == 2


async def test_limit_and_hidden_count():
    regions = [region(i, 10, 11, f"2020-01-{i % 28 + 1:02d} 00:00:00") for i in range(30)]
    res = await service(regions).occupied_for(10)
    assert len(res.shown) == MAX_REGIONS and res.total == 30
    text = format_rh("Italy", res, load_countries())
    assert "10 non mostrate" in text and "Totale regioni occupate: 30" in text


async def test_format_escapes_and_empty():
    res = await service([region(1, 10, 11, "2020-01-01 10:20:30")]).occupied_for(10)
    text = format_rh("It<aly>", res, load_countries())
    assert "It&lt;aly&gt; RHs" in text and "2020-01-01 10:20" in text
    empty = await service([]).occupied_for(10)
    assert "Nessuna regione" in format_rh("Italy", empty, load_countries())
