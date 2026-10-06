from __future__ import annotations

from dataclasses import dataclass

from .client import ErepToolsClient
from .models import Citizen, CitizenSummary

# Come in Socrates: oltre 9 omonimi chiediamo di restringere la ricerca.
MAX_CHOICES = 9


@dataclass(frozen=True, slots=True)
class Resolved:
    citizen: Citizen


@dataclass(frozen=True, slots=True)
class Ambiguous:
    candidates: list[CitizenSummary]


@dataclass(frozen=True, slots=True)
class TooMany:
    total: int


@dataclass(frozen=True, slots=True)
class NoMatch:
    pass


LookupResult = Resolved | Ambiguous | TooMany | NoMatch


class CitizenService:
    """Risolve 'id o nome' in un cittadino, senza sapere nulla di Telegram."""

    def __init__(self, client: ErepToolsClient) -> None:
        self._client = client

    async def get(self, citizen_id: int) -> Citizen:
        return await self._client.get_citizen(citizen_id)

    async def resolve(self, query: str) -> LookupResult:
        query = query.strip()
        if query.isdigit():
            return Resolved(await self._client.get_citizen(int(query)))

        page = await self._client.search_citizens(query)
        if page.total == 0 or not page.results:
            return NoMatch()
        if page.total == 1:
            return Resolved(await self._client.get_citizen(page.results[0].id))
        if page.total <= MAX_CHOICES:
            return Ambiguous(page.results)
        return TooMany(page.total)
