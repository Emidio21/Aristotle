from __future__ import annotations

from dataclasses import dataclass

from .client import ErepToolsClient
from .models import Region

MAX_REGIONS = 20  # come in Socrates (rh)


@dataclass(frozen=True, slots=True)
class OccupiedRegions:
    shown: list[Region]
    total: int


class RegionService:
    def __init__(self, client: ErepToolsClient) -> None:
        self._client = client

    async def occupied_for(self, country_id: int) -> OccupiedRegions:
        """Regioni sotto occupazione di cui il paese e' proprietario originale o attuale.

        Ordinate dalla piu' recentemente occupata.
        """
        picked = [
            r
            for r in await self._client.regions()
            if r.occupied_since
            and country_id in (r.original_owner_id, r.current_owner_id)
        ]
        picked.sort(key=lambda r: r.occupied_since or "", reverse=True)
        return OccupiedRegions(picked[:MAX_REGIONS], len(picked))
