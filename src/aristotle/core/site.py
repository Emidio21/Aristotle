from __future__ import annotations

import logging
import time

import httpx

from .client import ErepApiError

log = logging.getLogger(__name__)

CAMPAIGNS_URL = "https://www.erepublik.com/en/military/campaignsJson/list"
MAP_URL = "https://api.erepublik.com/map/data/"
USER_AGENT = "Aristotle-Telegram-Bot/0.1"


class SiteBlocked(ErepApiError):
    """erepublik.com ha risposto con una challenge anti-bot (Cloudflare) invece dei dati."""


def _is_blocked(resp: httpx.Response) -> bool:
    if resp.headers.get("cf-mitigated") == "challenge":
        return True
    return resp.status_code in (403, 429, 503) and "Just a moment" in resp.text[:2000]


class ErepSiteClient:
    """Client per gli endpoint pubblici di erepublik.com (campagne, mappa). Nessuna API key.

    Cache TTL breve in memoria: le battaglie cambiano di secondo in secondo, ma evitiamo di
    martellare il sito se piu' utenti lanciano i comandi insieme.
    """

    def __init__(
        self,
        *,
        cache_ttl: float = 20.0,
        timeout: float = 15.0,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self._ttl = cache_ttl
        self._http = http or httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        )
        self._owns_http = http is None
        self._cache: dict[str, tuple[float, str]] = {}

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def _get_text(self, url: str, ttl: float) -> str:
        now = time.monotonic()
        hit = self._cache.get(url)
        if hit and hit[0] > now:
            return hit[1]
        try:
            resp = await self._http.get(url)
        except httpx.HTTPError as exc:
            log.warning("Site request failed on %s: %s", url, type(exc).__name__)
            raise ErepApiError(type(exc).__name__) from None
        if _is_blocked(resp):
            log.warning("Site blocked by anti-bot challenge on %s (HTTP %s)", url, resp.status_code)
            raise SiteBlocked(f"HTTP {resp.status_code} challenge")
        if resp.status_code != 200:
            log.warning("Site HTTP %s on %s", resp.status_code, url)
            raise ErepApiError(f"HTTP {resp.status_code}")
        if ttl > 0:
            self._cache[url] = (now + ttl, resp.text)
        return resp.text

    async def campaigns_text(self) -> str:
        return await self._get_text(CAMPAIGNS_URL, self._ttl)

    async def map_text(self) -> str:
        # La mappa (MPP) cambia di rado: cache piu' lunga.
        return await self._get_text(MAP_URL, max(self._ttl, 300.0))
