import httpx
import pytest

from aristotle.core.client import CitizenNotFound, ErepApiError, ErepToolsClient

CITIZEN = {"citizen": {"id": 1, "name": "Plato", "is_alive": True, "registered": {"date": "2010-01-02 03:04"}, "level": 70}}


def make_client(handler, **kw):
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return ErepToolsClient(api_key="SECRET", http=http, **kw)


async def test_get_citizen_parses_and_sends_key():
    seen = {}

    def handler(request):
        seen["url"] = request.url
        return httpx.Response(200, json=CITIZEN)

    c = await make_client(handler).get_citizen(1)
    assert c.name == "Plato" and c.registered == "2010-01-02" and c.level == 70
    assert seen["url"].path == "/v0/citizen/1"
    assert seen["url"].params["key"] == "SECRET"


async def test_404_is_not_found():
    client = make_client(lambda r: httpx.Response(404))
    with pytest.raises(CitizenNotFound):
        await client.get_citizen(9)


async def test_missing_payload_is_not_found():
    client = make_client(lambda r: httpx.Response(200, json={"citizen": None}))
    with pytest.raises(CitizenNotFound):
        await client.get_citizen(9)


async def test_server_error_does_not_leak_key():
    client = make_client(lambda r: httpx.Response(500))
    with pytest.raises(ErepApiError) as ei:
        await client.get_citizen(1)
    assert "SECRET" not in str(ei.value)
    assert ei.value.__cause__ is None and ei.value.__suppress_context__


async def test_cache_avoids_second_request():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(200, json=CITIZEN)

    client = make_client(handler, cache_ttl=60)
    await client.get_citizen(1)
    await client.get_citizen(1)
    assert len(calls) == 1


async def test_search_encodes_name():
    seen = {}

    def handler(request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(
            200, json={"pagination": {"resultsTotal": 2}, "citizen": [{"id": 1, "name": "A B"}, {"id": 2, "name": "A B2"}]}
        )

    page = await make_client(handler).search_citizens("A B")
    assert seen["params"]["name"] == "A B"
    assert page.total == 2 and [r.id for r in page.results] == [1, 2]
