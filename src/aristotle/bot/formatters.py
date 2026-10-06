from __future__ import annotations

from html import escape

from ..core.countries import Countries
from ..core.data.ranks import air_rank, ground_rank
from ..core.models import Citizen, JobOffer, Offer
from ..core.regions import OccupiedRegions

POWERED_BY = '<i>Powered by <a href="https://erepublik.tools/en">erepublik.tools</a></i>'
PROFILE_URL ="https://www.erepublik.com/en/citizen/profile/"
MU_URL = "https://www.erepublik.com/en/military/military-unit/"
PARTY_URL = "https://www.erepublik.com/en/party/"
NEWSPAPER_URL = "https://www.erepublik.com/en/newspaper/"
JOBS_URL = "https://www.erepublik.com/en/economy/job-market/"
OFFER_URL = "https://www.erepublik.com/en/economy/marketplace/offer/"
AVATAR_URL = "https://avatar.erepublik.tools/citizen/{id}.jpg"


def avatar_url(citizen_id: int) -> str:
    return AVATAR_URL.format(id=citizen_id)


def _link(url: str, text: str) -> str:
    return f'<a href="{escape(url, quote=True)}">{escape(text)}</a>'


def format_citizen(c: Citizen) -> str:
    """Scheda cittadino in HTML Telegram (tutto il testo variabile e' escapato)."""
    rows: list[tuple[str, str | None]] = [
        ("Status", "Alive" if c.is_alive else "Dead"),
        ("Registered", c.registered or None),
        ("ID", str(c.id)),
        ("Level", None if c.level is None else str(c.level)),
        ("Division", None if c.division is None else str(c.division)),
        ("Citizenship", escape(c.citizenship_country_name) if c.citizenship_country_name else None),
        ("Military Unit", _link(f"{MU_URL}{c.mu_id}", c.mu_name) if c.mu_name else None),
        ("Party", _link(f"{PARTY_URL}{c.party_id}", c.party_name) if c.party_name else None),
        ("Strength", None if c.strength is None else str(c.strength)),
        ("Perception", None if c.perception is None else str(c.perception)),
        ("Rank", _esc_opt(ground_rank(c.rank_level))),
        ("Aircraft rank", _esc_opt(air_rank(c.rank_level_aircraft))),
        (
            "Newspaper",
            _link(f"{NEWSPAPER_URL}{c.newspaper_id}", c.newspaper_name)
            if c.newspaper_name
            else None,
        ),
    ]
    header = f"<b>{_link(f'{PROFILE_URL}{c.id}', c.name)}</b>"
    body = "\n".join(f"<b>{label}:</b> {value}" for label, value in rows if value)
    return f"{header}\n\n{body}\n\n{POWERED_BY}"


def _esc_opt(value: str | None) -> str | None:
    return escape(value) if value else None


def _num(value: float, decimals: int = 0) -> str:
    """Formato italiano: punto per le migliaia, virgola per i decimali (",00" omesso)."""
    text = f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return text.removesuffix(",00")


def format_offers(title: str, offers: list[Offer], countries: Countries) -> str:
    """Elenco delle migliori offerte di mercato in HTML Telegram."""
    if not offers:
        return f"<b>{escape(title)}</b>\nNessuna offerta.\n\n{POWERED_BY}"
    lines = [f"<b>{escape(title)}</b>"]
    for i, o in enumerate(offers, 1):
        lines.append(
            f"{i}. {countries.flag(o.country_id)} {escape(countries.name(o.country_id))} - "
            f"{_num(o.gross, 2)} (net {_num(o.net, 2)}) - "
            f"📦 {_link(OFFER_URL + str(o.id), _num(o.amount))}"
        )
    return "\n".join(lines) + "\n\n" + POWERED_BY


def format_jobs(title: str, offers: list[JobOffer], countries: Countries) -> str:
    """Elenco delle migliori offerte di lavoro in HTML Telegram."""
    if not offers:
        return f"<b>{escape(title)}</b>\nNessuna offerta.\n\n{POWERED_BY}"
    lines = [f"<b>{escape(title)}</b>"]
    for i, o in enumerate(offers, 1):
        limit = _num(o.salary_limit) if o.salary_limit else "∞"
        lines.append(
            f"{i}. {countries.flag(o.country_id)} {escape(countries.name(o.country_id))} - "
            f"{_num(o.gross, 2)} (net {_num(o.net, 2)}) - "
            f"💰 {_link(JOBS_URL + str(o.country_id), limit)}"
        )
    return "\n".join(lines) + "\n\n" + POWERED_BY


def format_rh(country: str, result: OccupiedRegions, countries: Countries) -> str:
    """Regioni occupate di un paese (originali o occupate da lui) in HTML Telegram."""
    title = f"<b>{escape(country)} RHs</b>"
    if not result.total:
        none = f"Nessuna regione sotto occupazione legata a {escape(country)}."
        return f"{title}\n{none}\n\n{POWERED_BY}"
    lines = [title]
    for i, r in enumerate(result.shown, 1):
        lines.append(
            f"{i}. {countries.flag(r.original_owner_id)} <b>{escape(r.name)}</b> "
            f"→ {countries.flag(r.current_owner_id)} "
            f"{escape(countries.name(r.current_owner_id))} "
            f"({escape((r.occupied_since or '')[:16])})"
        )
    footer = f"Totale regioni occupate: {result.total}"
    hidden = result.total - len(result.shown)
    if hidden:
        footer += f" ({hidden} non mostrate)"
    return "\n".join(lines) + "\n\n" + footer + "\n\n" + POWERED_BY


# --- Battaglie / MPP -------------------------------------------------------------------------

BATTLE_URL = "https://www.erepublik.com/en/military/battlefield/"
TG_LIMIT = 4000  # sotto i 4096 caratteri di Telegram, con margine


def paginate(title: str, lines: list[str], footer: str = POWERED_BY) -> list[str]:
    """Spezza un elenco in messaggi < TG_LIMIT; il footer va solo sull'ultimo."""
    chunks: list[list[str]] = [[]]
    size = len(title) + len(footer) + 4
    for line in lines:
        if chunks[-1] and size + len(line) + 1 > TG_LIMIT:
            chunks.append([])
            size = len(title) + len(footer) + 4
        chunks[-1].append(line)
        size += len(line) + 1
    out = []
    for i, chunk in enumerate(chunks):
        head = title if i == 0 else f"{title} ({i + 1})"
        tail = f"\n\n{footer}" if i == len(chunks) - 1 else ""
        out.append(head + "\n" + "\n".join(chunk) + tail)
    return out


def _mmss(seconds: int) -> str:
    return f"{seconds // 60}m{seconds % 60:02d}s"


def _battle_link(battle, text: str, div_id: str | None = None) -> str:
    url = f"{BATTLE_URL}{battle.id}" + (f"/{div_id}" if div_id else "")
    return _link(url, text)


def _flags(battle, countries: Countries) -> str:
    return f"{countries.flag(battle.inv_id)}-{countries.flag(battle.def_id)}"


def format_sh(rows, countries: Countries) -> list[str]:
    title = "<b>SHs</b>"
    if not rows:
        return [f"{title}\nNessun SH al momento.\n\n{POWERED_BY}"]
    lines = []
    for r in rows:
        head = f"{_flags(r.battle, countries)} {_battle_link(r.battle, escape(r.battle.region))}"
        if r.upcoming:
            lines.append(f"{head} - \U0001F6EB tra {_mmss(r.delay)}")
        else:
            lines.append(
                f"{head} - +{_mmss(r.started_since)} - "
                f"{_num(r.inv_damage)} / {_num(r.def_damage)}"
            )
    return paginate(title, lines)


def format_epics(rows, countries: Countries) -> list[str]:
    title = "<b>Epics</b>"
    if not rows:
        return [f"{title}\nNessuna epic o full-scale in corso.\n\n{POWERED_BY}"]
    lines = [
        f"{_flags(r.battle, countries)} {_battle_link(r.battle, escape(r.battle.region))} - "
        f"{r.kind}-D{r.division} - +{_mmss(r.started_since)}"
        for r in rows
    ]
    return paginate(title, lines)


def format_combat_orders(rows, countries: Countries) -> list[str]:
    title = "<b>Combat Orders</b>"
    if not rows:
        return [f"{title}\nNessun combat order al momento.\n\n{POWERED_BY}"]
    lines = []
    for r in rows:
        where = _battle_link(
            r.battle, f"D{r.division.number} {escape(r.battle.region)}", r.division.id
        )
        lines.append(
            f"{countries.flag(r.side_country_id)} {where} - "
            f"\U0001F4B0 {escape(r.order.reward)} ({escape(r.order.budget)}) - "
            f"{escape(r.order.threshold)}% ({r.wall:.2f}%)"
        )
    return paginate(title, lines)


def format_mpp(country: str, mpps, countries: Countries) -> list[str]:
    title = f"<b>{escape(country)} - Mutual Protection Pacts</b>"
    if not mpps:
        return [f"{title}\nNessun MPP.\n\n{POWERED_BY}"]
    lines = [
        f"{countries.flag(m.partner_id)} {escape(countries.name(m.partner_id))} - "
        f"{m.expires_iso}"
        for m in mpps
    ]
    return paginate(title, lines)


def mpps_csv(all_mpps, countries: Countries) -> str:
    """CSV 'paese;partner;gg/mm/aaaa' per tutti gli MPP (come mppsraw di Socrates)."""
    rows = [
        f"{countries.name(cid)};{countries.name(m.partner_id)};{m.expires_dmy}"
        for cid, mpps in all_mpps.items()
        for m in mpps
    ]
    return "\n".join(rows) + ("\n" if rows else "")
