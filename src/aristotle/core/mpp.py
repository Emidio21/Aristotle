from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from .client import ErepApiError
from .site import ErepSiteClient

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Mpp:
    partner_id: int
    expires: str  # "YYYYMMDD"

    @property
    def expires_iso(self) -> str:
        return f"{self.expires[:4]}-{self.expires[4:6]}-{self.expires[6:8]}"

    @property
    def expires_dmy(self) -> str:
        return f"{self.expires[6:8]}/{self.expires[4:6]}/{self.expires[:4]}"


def _as_list(value: object) -> list:
    """Il JSON (convertito da XML) usa un dict se c'e' un solo elemento, " " se non ce ne sono."""
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def parse_map(text: str) -> dict[int, list[Mpp]]:
    """country_id -> MPP ordinati per scadenza, dal JSON di map/data."""
    try:
        countries = _as_list(json.loads(text)["message"]["countries"]["country"])
        result: dict[int, list[Mpp]] = {}
        for country in countries:
            cid = int(country["%c_id%"])
            mpps_node = country.get("mpps")
            raw = _as_list(mpps_node.get("mpp")) if isinstance(mpps_node, dict) else []
            mpps = [Mpp(int(m["%c_id%"]), str(m["%expires%"])) for m in raw]
            result[cid] = sorted(mpps, key=lambda m: m.expires)
        return result
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        log.warning("Unexpected map payload (%s): %.200r", type(exc).__name__, text)
        raise ErepApiError("unexpected map payload") from None


class MppService:
    def __init__(self, site: ErepSiteClient) -> None:
        self._site = site

    async def all(self) -> dict[int, list[Mpp]]:
        return parse_map(await self._site.map_text())

    async def for_country(self, country_id: int) -> list[Mpp]:
        return (await self.all()).get(country_id, [])
