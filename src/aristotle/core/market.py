from __future__ import annotations

from dataclasses import dataclass

from .client import ErepToolsClient
from .models import JobOffer, Offer

MAX_OFFERS = 10
MAX_QUALITY = 7


@dataclass(frozen=True, slots=True)
class MarketItem:
    command: str
    item_id: int
    title: str
    # None: la qualita' e' richiesta all'utente; altrimenti e' fissa (es. i raw material).
    fixed_quality: int | None = None


# Come in Socrates (market.py): comando -> id industria eRepublik.
MARKET_ITEMS: tuple[MarketItem, ...] = (
    MarketItem("food", 1, "Food"),
    MarketItem("weapons", 2, "Weapons"),
    MarketItem("tickets", 3, "Tickets"),
    MarketItem("houses", 4, "Houses"),
    MarketItem("aircrafts", 23, "Aircrafts"),
    MarketItem("frm", 7, "Food raw material", fixed_quality=1),
    MarketItem("wrm", 12, "Weapon raw material", fixed_quality=1),
    MarketItem("hrm", 17, "House raw material", fixed_quality=1),
    MarketItem("arm", 24, "Aircraft raw material", fixed_quality=1),
)


class InvalidQuality(ValueError):
    pass


def parse_quality(text: str) -> int:
    try:
        q = int(text.strip())
    except ValueError:
        raise InvalidQuality(text) from None
    if not 1 <= q <= MAX_QUALITY:
        raise InvalidQuality(text)
    return q


class MarketService:
    def __init__(self, client: ErepToolsClient) -> None:
        self._client = client

    async def best_offers(self, item: MarketItem, quality: int) -> list[Offer]:
        offers = await self._client.best_offers(item.item_id, quality)
        return offers[:MAX_OFFERS]

    async def job_offers(self, country_id: int | None = None) -> list[JobOffer]:
        offers = await self._client.job_offers(country_id)
        return offers[:MAX_OFFERS]
