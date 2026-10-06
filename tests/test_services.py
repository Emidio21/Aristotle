from aristotle.core.client import SearchPage
from aristotle.core.models import Citizen, CitizenSummary
from aristotle.core.services import Ambiguous, CitizenService, NoMatch, Resolved, TooMany


class FakeClient:
    def __init__(self, total=0, n_results=0):
        self.total = total
        self.n = n_results

    async def get_citizen(self, cid):
        return Citizen(id=cid, name=f"c{cid}")

    async def search_citizens(self, name, page=1):
        return SearchPage(self.total, [CitizenSummary(i, f"{name}{i}") for i in range(1, self.n + 1)])


async def test_numeric_query_goes_by_id():
    r = await CitizenService(FakeClient()).resolve("42")
    assert isinstance(r, Resolved) and r.citizen.id == 42


async def test_no_match():
    assert isinstance(await CitizenService(FakeClient(0, 0)).resolve("x"), NoMatch)


async def test_single_match_resolves():
    r = await CitizenService(FakeClient(1, 1)).resolve("x")
    assert isinstance(r, Resolved) and r.citizen.id == 1


async def test_ambiguous_up_to_nine():
    r = await CitizenService(FakeClient(9, 9)).resolve("x")
    assert isinstance(r, Ambiguous) and len(r.candidates) == 9


async def test_too_many():
    r = await CitizenService(FakeClient(10, 10)).resolve("x")
    assert isinstance(r, TooMany) and r.total == 10
