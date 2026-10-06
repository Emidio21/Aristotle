from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .client import ErepApiError
from .site import ErepSiteClient

# Soglia di danno sotto la quale un round aereo gia' iniziato e' "SH" (come in Socrates).
SH_DAMAGE_THRESHOLD = 30000


def _int(v: Any, default: int = 0) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True, slots=True)
class CombatOrder:
    co_id: str
    reward: str
    budget: str
    threshold: str


@dataclass(frozen=True, slots=True)
class Division:
    id: str
    number: int
    epic: int  # 0 = no, 1 = fullscale, 2 = epic
    epic_type: int
    ended: bool
    inv_damage: int
    def_damage: int
    co_inv: tuple[CombatOrder, ...]
    co_def: tuple[CombatOrder, ...]
    wall_for: int | None
    wall_dom: float


@dataclass(frozen=True, slots=True)
class Battle:
    id: int
    type: str
    start: int
    inv_id: int
    def_id: int
    region: str
    divisions: tuple[Division, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class Campaigns:
    time: int
    battles: tuple[Battle, ...]


def _orders(raw: Any) -> tuple[CombatOrder, ...]:
    if not isinstance(raw, list):
        return ()
    return tuple(
        CombatOrder(
            co_id=str(o.get("co_id")),
            reward=str(o.get("reward", "")),
            budget=str(o.get("budget", "")),
            threshold=str(o.get("threshold", "")),
        )
        for o in raw
        if isinstance(o, dict)
    )


def _division(div_id: str, d: dict[str, Any]) -> Division:
    stats = d.get("stats") or {}
    inv = stats.get("inv") or {}
    dfn = stats.get("def") or {}
    co = d.get("co") or {}
    wall = d.get("wall") or {}
    wall_for = wall.get("for")
    return Division(
        id=str(div_id),
        number=_int(d.get("div")),
        epic=_int(d.get("epic")),
        epic_type=_int(d.get("epic_type")),
        ended=bool(d.get("division_end")),
        inv_damage=_int(inv.get("damage")),
        def_damage=_int(dfn.get("damage")),
        co_inv=_orders(co.get("inv")),
        co_def=_orders(co.get("def")),
        wall_for=None if wall_for is None else _int(wall_for),
        wall_dom=_float(wall.get("dom")),
    )


def parse_campaigns(text: str) -> Campaigns:
    """Parsa il JSON di campaignsJson/list. Solleva ErepApiError se la forma e' inattesa."""
    try:
        data = json.loads(text)
        battles = []
        for raw in data["battles"].values():
            divs = tuple(_division(k, v) for k, v in (raw.get("div") or {}).items())
            battles.append(
                Battle(
                    id=_int(raw["id"]),
                    type=str(raw.get("type", "")),
                    start=_int(raw.get("start")),
                    inv_id=_int(raw["inv"]["id"]),
                    def_id=_int(raw["def"]["id"]),
                    region=str((raw.get("region") or {}).get("name", "?")),
                    divisions=divs,
                )
            )
        return Campaigns(time=_int(data["time"]), battles=tuple(battles))
    except (ValueError, KeyError, TypeError, AttributeError):
        raise ErepApiError("unexpected campaigns payload") from None


@dataclass(frozen=True, slots=True)
class ShRow:
    battle: Battle
    delay: int  # secondi all'inizio (> 0: non ancora iniziato)
    started_since: int  # secondi dall'inizio (0 se non iniziato)
    inv_damage: int
    def_damage: int

    @property
    def upcoming(self) -> bool:
        return self.delay > 0


@dataclass(frozen=True, slots=True)
class EpicRow:
    battle: Battle
    division: int
    kind: str  # "Epic" | "Fullscale" | "Most Contested"
    started_since: int


@dataclass(frozen=True, slots=True)
class CoRow:
    battle: Battle
    side_country_id: int
    division: Division
    order: CombatOrder
    wall: float  # % di dominio del lato che ha il CO


def select_sh(c: Campaigns) -> list[ShRow]:
    """Round aerei in arrivo, oppure gia' iniziati con danno basso (< soglia) su un lato."""
    rows = []
    for b in c.battles:
        if b.type != "aircraft" or not b.divisions:
            continue
        delay = b.start - c.time
        if delay > 0:
            rows.append(ShRow(b, delay, 0, 0, 0))
            continue
        d = b.divisions[0]
        if d.inv_damage < SH_DAMAGE_THRESHOLD or d.def_damage < SH_DAMAGE_THRESHOLD:
            rows.append(ShRow(b, delay, -delay, d.inv_damage, d.def_damage))
    rows.sort(key=lambda r: -r.delay)
    return rows


def select_epics(c: Campaigns) -> list[EpicRow]:
    rows = []
    for b in c.battles:
        if not any(d.epic and not d.ended for d in b.divisions):
            continue
        for d in b.divisions:
            if not d.epic:
                continue
            if d.epic == 2:
                kind = "Most Contested" if d.epic_type == 5 else "Epic"
            else:
                kind = "Fullscale"
            rows.append(EpicRow(b, d.number, kind, c.time - b.start))
    return rows


def select_combat_orders(c: Campaigns) -> list[CoRow]:
    """Combat order per lato, senza duplicati tra divisioni (stesso co_id)."""
    rows = []
    for b in c.battles:
        for side_id, attr in ((b.inv_id, "co_inv"), (b.def_id, "co_def")):
            seen: set[str] = set()
            for d in b.divisions:
                for order in getattr(d, attr):
                    if order.co_id in seen:
                        continue
                    seen.add(order.co_id)
                    wall = d.wall_dom if d.wall_for == side_id else 100 - d.wall_dom
                    rows.append(CoRow(b, side_id, d, order, wall))
    return rows


class BattleService:
    def __init__(self, site: ErepSiteClient) -> None:
        self._site = site

    async def _campaigns(self) -> Campaigns:
        return parse_campaigns(await self._site.campaigns_text())

    async def sh(self) -> list[ShRow]:
        return select_sh(await self._campaigns())

    async def epics(self) -> list[EpicRow]:
        return select_epics(await self._campaigns())

    async def combat_orders(self) -> list[CoRow]:
        return select_combat_orders(await self._campaigns())
