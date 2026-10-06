from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .models import Citizen, CitizenSummary, JobOffer, Offer, Region

log = logging.getLogger(__name__)

_MAX_CACHE_ENTRIES = 512


class ErepApiError(Exception):
    """Errore generico del servizio dati (rete, HTTP, payload non valido).

    `code` e' il codice d'errore applicativo dell'API (es. E_CITIZEN_NOT_FOUND), se presente.
    """

    def __init__(self, message: str = "", code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class CitizenNotFound(ErepApiError):
    """Il cittadino richiesto non esiste."""


class InvalidRequest(ErepApiError):
    """L'API ha rifiutato i parametri (HTTP 400), es. combinazione item/qualita' non valida."""


@dataclass(frozen=True, slots=True)
class SearchPage:
    total: int
    results: list[CitizenSummary]


def _error_code(resp: httpx.Response) -> str | None:
    """Estrae il codice d'errore dal body: {"message": "E_X"} oppure {"errors":[{"message": "E_X"}]}."""
    try:
        body = resp.json()
        if isinstance(body.get("message"), str):
            return body["message"]
        return str(body["errors"][0]["message"])
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        return None


class ErepToolsClient:
    """Client async per api.erepublik.tools, con cache TTL in memoria.

    NB: la API key viaggia come query param (come in Socrates). Per questo le eccezioni
    httpx NON vengono concatenate (`from None`): il loro messaggio contiene l'URL completo.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.erepublik.tools",
        version: str = "v0",
        search_version: str = "v0",
        cache_ttl: float = 60.0,
        timeout: float = 10.0,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self._key = api_key
        self._base = base_url.rstrip("/")
        self._version = version
        self._search_version = search_version
        self._ttl = cache_ttl
        self._http = http or httpx.AsyncClient(timeout=timeout)
        self._owns_http = http is None
        self._cache: dict[tuple, tuple[float, Any]] = {}

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}
        cache_key = (path, tuple(sorted(params.items())))
        now = time.monotonic()
        hit = self._cache.get(cache_key)
        if hit and hit[0] > now:
            return hit[1]

        try:
            resp = await self._http.get(
                f"{self._base}{path}", params={**params, "key": self._key}
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            log.warning("API HTTP %s on %s", status, path)
            if status == 404:
                raise CitizenNotFound(path) from None
            if status == 400:
                code = _error_code(exc.response)
                if code == "E_CITIZEN_NOT_FOUND":
                    raise CitizenNotFound(path) from None
                raise InvalidRequest(f"HTTP 400 {code or ''}".strip(), code) from None
            raise ErepApiError(f"HTTP {status}") from None
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("API request failed on %s: %s", path, type(exc).__name__)
            raise ErepApiError(type(exc).__name__) from None

        if self._ttl > 0:
            if len(self._cache) >= _MAX_CACHE_ENTRIES:
                self._cache = {k: v for k, v in self._cache.items() if v[0] > now}
            self._cache[cache_key] = (now + self._ttl, data)
        return data

    async def get_citizen(self, citizen_id: int) -> Citizen:
        data = await self._get(f"/{self._version}/citizen/{int(citizen_id)}")
        raw = data.get("citizen") if isinstance(data, dict) else None
        if not isinstance(raw, dict) or "id" not in raw:
            raise CitizenNotFound(str(citizen_id))
        return Citizen.from_api(raw)

    async def search_citizens(self, name: str, page: int = 1) -> SearchPage:
        data = await self._get(
            f"/{self._search_version}/citizen", {"name": name, "page": page}
        )
        try:
            total = int(data["pagination"]["resultsTotal"])
            rows = data.get("citizen") or []
            results = [CitizenSummary(id=int(r["id"]), name=str(r["name"])) for r in rows]
        except (KeyError, TypeError, ValueError):
            raise ErepApiError("unexpected search payload") from None
        return SearchPage(total=total, results=results)

    async def best_offers(self, item_id: int, quality: int) -> list[Offer]:
        """Migliori offerte di mercato per un item/qualita' (gia' ordinate dall'API)."""
        data = await self._get(
            f"/{self._version}/market/item/best-offers/{int(item_id)}/{int(quality)}"
        )
        try:
            return [Offer.from_api(o) for o in data["offers"]]
        except (KeyError, TypeError, ValueError):
            raise ErepApiError("unexpected offers payload") from None

    async def job_offers(self, country_id: int | None = None) -> list[JobOffer]:
        """Migliori offerte di lavoro, mondiali o di un paese."""
        target = "best-offers" if country_id is None else str(int(country_id))
        data = await self._get(f"/{self._version}/market/job/{target}")
        try:
            return [JobOffer.from_api(o) for o in data["offers"]]
        except (KeyError, TypeError, ValueError):
            raise ErepApiError("unexpected jobs payload") from None

    async def regions(self) -> list[Region]:
        """Tutte le regioni (payload grande: sfrutta la cache TTL)."""
        data = await self._get(f"/{self._version}/region/list")
        try:
            return [Region.from_api(r) for r in data["regions"]]
        except (KeyError, TypeError, ValueError):
            raise ErepApiError("unexpected regions payload") from None
