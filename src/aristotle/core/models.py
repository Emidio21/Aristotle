from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CitizenSummary:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class Citizen:
    id: int
    name: str
    is_alive: bool = True
    registered: str = ""
    level: int | None = None
    division: int | None = None
    citizenship_country_id: int | None = None
    citizenship_country_name: str | None = None
    mu_id: int | None = None
    mu_name: str | None = None
    party_id: int | None = None
    party_name: str | None = None
    newspaper_id: int | None = None
    newspaper_name: str | None = None
    strength: int | float | None = None
    perception: int | float | None = None
    rank_level: int | None = None
    rank_level_aircraft: int | None = None

    @classmethod
    def from_api(cls, d: dict[str, Any]) -> Citizen:
        registered = d.get("registered")
        registered_date = registered.get("date", "") if isinstance(registered, dict) else ""
        return cls(
            id=int(d["id"]),
            name=str(d["name"]),
            is_alive=bool(d.get("is_alive", True)),
            registered=registered_date[:10],
            level=d.get("level"),
            division=d.get("division"),
            citizenship_country_id=d.get("citizenship_country_id"),
            citizenship_country_name=d.get("citizenship_country_name"),
            mu_id=d.get("mu_id"),
            mu_name=d.get("mu_name") or None,
            party_id=d.get("party_id"),
            party_name=d.get("party_name") or None,
            newspaper_id=d.get("newspaper_id"),
            newspaper_name=d.get("newspaper_name") or None,
            strength=d.get("strength"),
            perception=d.get("perception"),
            rank_level=d.get("rank_level"),
            rank_level_aircraft=d.get("rank_level_aircraft"),
        )


@dataclass(frozen=True, slots=True)
class Offer:
    id: int
    country_id: int
    amount: int
    gross: float
    net: float

    @classmethod
    def from_api(cls, d: dict[str, Any]) -> Offer:
        return cls(
            id=int(d["id"]),
            country_id=int(d["country_id"]),
            amount=int(d["amount"]),
            gross=float(d["gross"]),
            net=float(d["net"]),
        )


@dataclass(frozen=True, slots=True)
class JobOffer:
    country_id: int
    citizen_id: int
    citizen_name: str
    gross: float
    net: float
    salary_limit: int  # 0 = illimitato

    @classmethod
    def from_api(cls, d: dict[str, Any]) -> JobOffer:
        return cls(
            country_id=int(d["country_id"]),
            citizen_id=int(d["citizen_id"]),
            citizen_name=str(d.get("citizen_name") or ""),
            gross=float(d["gross"]),
            net=float(d["net"]),
            salary_limit=int(d.get("salary_limit") or 0),
        )


@dataclass(frozen=True, slots=True)
class Region:
    id: int
    name: str
    original_owner_id: int
    current_owner_id: int
    occupied_since: str | None  # "YYYY-MM-DD HH:MM:SS", None se non occupata

    @classmethod
    def from_api(cls, d: dict[str, Any]) -> Region:
        since = d.get("under_occupation_since")
        return cls(
            id=int(d["id"]),
            name=str(d["name"]),
            original_owner_id=int(d["original_owner_country_id"]),
            current_owner_id=int(d["current_owner_country_id"]),
            occupied_since=str(since["date"])[:19] if isinstance(since, dict) else None,
        )
