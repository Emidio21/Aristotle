from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from .client import ErepApiError
from .site import ErepSiteClient


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


def parse_map(text: str) -> dict[int, list[Mpp]]:
    """country_id -> MPP ordinati per scadenza, dall'XML di map/data."""
    try:
        root = ET.fromstring(text)
        result: dict[int, list[Mpp]] = {}
        for country in root.iter("country"):
            cid = int(country.attrib["c_id"])
            mpps = [
                Mpp(int(m.attrib["c_id"]), m.attrib["expires"])
                for m in country.iter("mpp")
            ]
            result[cid] = sorted(mpps, key=lambda m: m.expires)
        return result
    except (ET.ParseError, KeyError, ValueError):
        raise ErepApiError("unexpected map payload") from None


class MppService:
    def __init__(self, site: ErepSiteClient) -> None:
        self._site = site

    async def all(self) -> dict[int, list[Mpp]]:
        return parse_map(await self._site.map_text())

    async def for_country(self, country_id: int) -> list[Mpp]:
        return (await self.all()).get(country_id, [])
