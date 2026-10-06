from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files


@dataclass(frozen=True, slots=True)
class Country:
    id: int
    name: str
    code: str  # ISO-3166 alpha-2 minuscolo, es. "it"

    @property
    def flag(self) -> str:
        """Emoji bandiera (due regional indicator unicode)."""
        return "".join(chr(0x1F1E6 + ord(c) - ord("a")) for c in self.code)


class Countries:
    """Elenco paesi eRepublik (id <-> nome <-> bandiera). Dati da countries.csv di Socrates."""

    def __init__(self, countries: list[Country]) -> None:
        self._by_id = {c.id: c for c in countries}
        self._all = countries

    def get(self, country_id: int) -> Country | None:
        return self._by_id.get(country_id)

    def name(self, country_id: int) -> str:
        c = self.get(country_id)
        return c.name if c else f"#{country_id}"

    def flag(self, country_id: int) -> str:
        c = self.get(country_id)
        return c.flag if c else "\U0001F3F3"

    def find(self, query: str) -> list[Country]:
        """Match case-insensitive: prima i nomi uguali, altrimenti quelli che contengono la query."""
        q = query.strip().casefold()
        if not q:
            return []
        exact = [c for c in self._all if c.name.casefold() == q]
        if exact:
            return exact
        return [c for c in self._all if q in c.name.casefold()]


@lru_cache(maxsize=1)
def load_countries() -> Countries:
    path = files("aristotle.core.data").joinpath("countries.csv")
    rows: list[Country] = []
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh, delimiter=";", quotechar='"'):
            if len(row) < 3:
                continue
            code = row[2].strip().removeprefix(":flag_").removesuffix(":")
            rows.append(Country(id=int(row[0]), name=row[1], code=code))
    return Countries(rows)
