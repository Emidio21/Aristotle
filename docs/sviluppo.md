# Aristotle - note tecniche

Bot Telegram per il browser game [eRepublik](https://www.erepublik.com), port del bot Discord
[Socrates](https://github.com/Curlybear/Socrates) (Curlybear). Nome in tema: Socrates (Discord),
Plato (bot admin in-game), Aristotle (Telegram).

Dati da [erepublik.tools](https://erepublik.tools/en) (Powered by erepublik.tools) e, per
battaglie e MPP, dagli endpoint pubblici di erepublik.com.

## Licenza e attribuzione

GPL-3.0-or-later (file `LICENSE`), come Socrates di cui questo progetto e' un'opera derivata.
Provengono da Socrates: la logica dei comandi, `core/data/countries.csv` e
`core/data/ranks.py`.

## Comandi

| Comando | Descrizione | Fonte |
|---|---|---|
| `/user <id o nome>` | Scheda cittadino (omonimi: tastiera di scelta) | erepublik.tools |
| `/food` `/weapons` `/tickets` `/houses` `/aircrafts <q 1-7>` | Migliori offerte di mercato | erepublik.tools |
| `/frm` `/wrm` `/hrm` `/arm` | Migliori offerte raw material | erepublik.tools |
| `/jobs [paese]` | Migliori offerte di lavoro | erepublik.tools |
| `/rh <paese>` | Regioni occupate | erepublik.tools |
| `/sh` `/epic` `/co` | Round aerei, epic/full-scale, combat order | erepublik.com (*) |
| `/mpp <paese>` `/mppsraw` | MPP di un paese / CSV di tutti | erepublik.com (*) |
| `/convert <eRep day \| gg/mm/aaaa>` | Conversione giorno eRepublik <-> data | locale |
| `/ping` `/help` | | locale |

(*) erepublik.com e' protetto da una challenge anti-bot Cloudflare: da alcuni IP/client le richieste
vengono rifiutate (HTTP 403). In quel caso il bot lo dice all'utente. Verificare dal server di
produzione. Non c'e' alcun tentativo di aggirare la protezione.

## Avvio rapido

Richiede Python >= 3.11, un token da [@BotFather](https://t.me/BotFather) e una API key di erepublik.tools.

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env     # compila ARISTOTLE_TELEGRAM_TOKEN e ARISTOTLE_EREP_API_KEY
pytest && ruff check src tests
python -m aristotle
```

Il file `.env` e' ignorato da git: non committarlo mai. La API key viaggia come query param verso
erepublik.tools, quindi il codice non la logga mai (logger httpx a WARNING, eccezioni con `from None`).

## Architettura

```
src/aristotle/
  config.py       # impostazioni da env (pydantic-settings)
  core/           # nessuna dipendenza da Telegram
    client.py     # ErepToolsClient: httpx async, cache TTL, errori tipizzati
    site.py       # ErepSiteClient: erepublik.com (campagne, mappa), rileva la challenge
    services.py market.py regions.py battles.py mpp.py erepday.py countries.py
    data/         # countries.csv, ranks.py
  bot/            # adapter Telegram
    app.py        # cablaggio: servizi + handler + menu comandi
    handlers/     # un modulo per area (user, market, region, war, meta, basic)
    formatters.py # HTML Telegram (tutto il testo variabile e' escapato)
```

Ogni comando segue la catena client -> service -> formatter -> handler, con test unitari su
trasporto simulato (`httpx.MockTransport`).

## Stato

- [x] `/user`, mercato, `/jobs`, `/rh`, `/convert`, `/ping`, `/help`
- [x] `/sh`, `/epic`, `/co`, `/mpp`, `/mppsraw` (scritti sul formato di Socrates, provati solo su
      dati simulati: da verificare con risposte reali di erepublik.com)
- [x] Nomi dei rank copiati da Socrates (`core/data/ranks.py`)
- [ ] Storico (`history`): dipende da erep-d, in outage (disabilitato anche in Socrates)
- [ ] Docker, CI, notifiche battaglie (JobQueue + DB iscrizioni)

## Deploy con Docker

```bash
cp .env.example .env && chmod 600 .env     # compila token e API key
docker compose up -d --build
docker compose logs -f aristotle
```

- Nessuna porta esposta: il bot usa il long polling. **Una sola istanza per token** (un'istanza di
  sviluppo accesa in parallelo causa errori di conflitto).
- Container non-root, filesystem read-only, nessuna capability, log con rotazione.
- Aggiornamento: `git pull && docker compose up -d --build`.
- Prima di contare su `/sh /epic /co /mpp /mppsraw`, verificare dal server che erepublik.com non risponda 403:
  `curl -s -o /dev/null -w "%{http_code}\n" https://www.erepublik.com/en/military/campaignsJson/list`
