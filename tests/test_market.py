import httpx
import pytest

from aristotle.bot.formatters import format_offers
from aristotle.core.client import CitizenNotFound, ErepToolsClient, InvalidRequest
from aristotle.core.countries import load_countries
from aristotle.core.market import MARKET_ITEMS, InvalidQuality, MarketService, parse_quality

OFFER = {"id": 7, "country_id": 10, "amount": 5, "net": 0.9, "gross": 0.93, "added": "x"}


def make_client(handler):
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return ErepToolsClient(api_key="SECRET", http=http)


def test_countries_loaded_and_flag():
    c = load_countries()
    assert c.name(10) == "Italy"
    assert c.flag(10) == "\U0001F1EE\U0001F1F9"
    assert c.name(99999) == "#99999"


def test_countries_find():
    c = load_countries()
    assert [x.id for x in c.find("italy")] == [10]
    assert c.find("zzzz") == []
    assert len(c.find("a")) > 1


def test_parse_quality():
    assert parse_quality(" 3 ") == 3
    for bad in ("", "x", "0", "8", "1.5"):
        with pytest.raises(InvalidQuality):
            parse_quality(bad)


def test_market_items_unique():
    assert len({i.command for i in MARKET_ITEMS}) == len(MARKET_ITEMS)
    assert len({i.item_id for i in MARKET_ITEMS}) == len(MARKET_ITEMS)


async def test_best_offers_url_and_limit():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        return httpx.Response(200, json={"offers": [OFFER] * 30})

    svc = MarketService(make_client(handler))
    food = next(i for i in MARKET_ITEMS if i.command == "food")
    offers = await svc.best_offers(food, 2)
    assert seen["path"] == "/v0/market/item/best-offers/1/2"
    assert len(offers) == 10 and offers[0].gross == 0.93


async def test_fewer_than_ten_offers_ok():
    svc = MarketService(make_client(lambda r: httpx.Response(200, json={"offers": [OFFER]})))
    assert len(await svc.best_offers(MARKET_ITEMS[0], 1)) == 1


async def test_400_invalid_quality_code():
    body = {"status": "error", "message": "E_INVALID_INDUSTRY_QUALITY_COMBINATION"}
    client = make_client(lambda r: httpx.Response(400, json=body))
    with pytest.raises(InvalidRequest) as exc:
        await client.best_offers(1, 9)
    assert exc.value.code == "E_INVALID_INDUSTRY_QUALITY_COMBINATION"
    assert "SECRET" not in str(exc.value)


async def test_400_citizen_not_found_maps_to_not_found():
    body = {"status": "error", "errors": [{"path": "_status", "message": "E_CITIZEN_NOT_FOUND"}]}
    client = make_client(lambda r: httpx.Response(400, json=body))
    with pytest.raises(CitizenNotFound):
        await client.get_citizen(1)


async def test_format_offers_escapes_and_links():
    offers = await MarketService(
        make_client(lambda r: httpx.Response(200, json={"offers": [OFFER]}))
    ).best_offers(MARKET_ITEMS[0], 1)
    text = format_offers("Food <Q1>", offers, load_countries())
    assert "Food &lt;Q1&gt;" in text and "Italy" in text
    assert "marketplace/offer/7" in text


def test_format_offers_empty():
    assert "Nessuna offerta" in format_offers("Food Q1", [], load_countries())


def test_number_format_italian():
    from aristotle.bot.formatters import _num

    assert _num(150999) == "150.999"
    assert _num(36397.0, 2) == "36.397"
    assert _num(0.93, 2) == "0,93"
    assert _num(1234.5, 2) == "1.234,50"


JOB = {"country_id": 10, "citizen_id": 3, "citizen_name": "Bob", "gross": 7860, "net": 7781.4,
       "salary_limit": 0}


async def test_job_offers_urls():
    seen = []

    def handler(request):
        seen.append(request.url.path)
        return httpx.Response(200, json={"offers": [JOB] * 15})

    svc = MarketService(make_client(handler))
    assert len(await svc.job_offers()) == 10
    await svc.job_offers(10)
    assert seen == ["/v0/market/job/best-offers", "/v0/market/job/10"]


def test_format_jobs_unlimited_and_limit():
    from aristotle.bot.formatters import format_jobs
    from aristotle.core.models import JobOffer

    a = JobOffer.from_api(JOB)
    b = JobOffer.from_api({**JOB, "salary_limit": 12000})
    text = format_jobs("Jobs <x>", [a, b], load_countries())
    assert "Jobs &lt;x&gt;" in text and "∞" in text and "12.000" in text
    assert "job-market/10" in text
    assert "Nessuna offerta" in format_jobs("J", [], load_countries())


def test_powered_by_footer_everywhere():
    from aristotle.bot.formatters import POWERED_BY, format_jobs, format_rh
    from aristotle.core.models import JobOffer, Offer
    from aristotle.core.regions import OccupiedRegions

    cs = load_countries()
    assert "https://erepublik.tools/en" in POWERED_BY
    offer = Offer(1, 10, 5, 1.0, 1.0)
    job = JobOffer.from_api(JOB)
    outputs = [
        format_offers("T", [offer], cs),
        format_offers("T", [], cs),
        format_jobs("T", [job], cs),
        format_jobs("T", [], cs),
        format_rh("Italy", OccupiedRegions([], 0), cs),
    ]
    assert all(o.endswith(POWERED_BY) for o in outputs)
