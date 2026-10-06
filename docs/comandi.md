> Aggiornamento: tutti i comandi della tabella sono stati portati (vedi [sviluppo.md](sviluppo.md)). Restano da verificare
> su dati reali /sh /epic /co /mpp /mppsraw (erepublik.com dietro Cloudflare).

# Comandi Socrates -> Aristotle (TODO 3)

Verificato il 2026-10-04 con key reale. Base tools: `https://api.erepublik.tools/v0` (+ `?key=`).
Fonte: Socrates `battle.py`, `market.py`, `country.py`, `meta.py`, `ereputils.py`.

| Comando | Endpoint | Stato | Prio |
|---|---|---|---|
| `/user` | `/citizen/{id}`, `/citizen?name=` | FATTO, provato su Telegram | - |
| `/food <q>` | `/market/item/best-offers/1/{q}` | vivo (200) | 1 |
| `/weapons <q>` | `/market/item/best-offers/2/{q}` | vivo | 1 |
| `/aircrafts <q>` | `/market/item/best-offers/23/{q}` | vivo | 1 |
| `/houses <q>` | `/market/item/best-offers/4/{q}` | vivo | 1 |
| `/tickets <q>` | `/market/item/best-offers/3/{q}` | vivo | 1 |
| `/frm` `/wrm` `/hrm` `/arm` | `/market/item/best-offers/{7,12,17,24}/1` | vivo | 1 |
| `/jobs [paese]` | `/market/job/best-offers` oppure `/market/job/{country_id}` | vivo | 1 |
| `/rh <paese>` | `/region/list` (filtro su `original/current_owner_country_id` + `under_occupation_since`) | vivo | 2 |
| `/sh` `/epic` `/co` | `https://www.erepublik.com/en/military/campaignsJson/list` | **403 Cloudflare** da curl | 3 (bloccato) |
| `/mpp <paese>` `/mppsraw` | `http://api.erepublik.com/map/data/` (XML) | **301 -> 403 Cloudflare** | 3 (bloccato) |
| `/convert` | nessuno (calcolo locale, epoch eRep day 1 = 2007-11-21) | solo logica | 1 (facile) |
| `/ping` | nessuno | FATTO | - |
| `/invite`, `/botinfo`, `/itfw` | nessuno (specifici di Discord / meme) | non portare | - |

## Note
- Mercato: risposta `{"offers":[{id,country_id,amount,net,gross,added}]}`. Socrates cicla `range(10)` senza
  controllare la lunghezza: noi dobbiamo usare `offers[:10]`. Link offerta:
  `https://www.erepublik.com/en/economy/marketplace/offer/{id}`.
- Jobs: offers con `country_id, citizen_id, citizen_name, gross, net, salary_limit (0 = illimitato)`.
- Paesi: Socrates risolve il nome con `LIKE %nome%` su SQLite (`countries.csv`). Serve `core/data/countries.csv`
  (TODO 2, non ancora copiato) e una funzione id<->nome<->bandiera nel core. Va gestito il caso nessun match
  (Socrates solleva eccezione) e piu' match (prendere il primo o disambiguare).
- Item id: 1 food, 2 weapons, 3 tickets, 4 houses, 7 FRM, 12 WRM, 17 HRM, 23 aircrafts, 24 ARM. Qualita' 1-7
  (5 per weapons/aircrafts negli esempi), validare che `q` sia un intero.
- Battaglie e MPP dipendono da erepublik.com dietro Cloudflare: da `curl` rispondono 403 (challenge). Da provare
  con httpx + header browser, ma probabilmente serve un'alternativa (cercare un endpoint equivalente su
  erepublik.tools, es. `/battle/...` o `/country/...`, da scoprire) oppure rinunciare.
- Storico (`history`) resta disabilitato (erep-d in outage).

## Ordine proposto
1. Paesi (countries.csv + util) -> 2. mercato (un solo client method generico `best_offers(item, q)`, un solo
formatter, 9 comandi come tabella di config) -> 3. `/jobs` -> 4. `/convert` -> 5. `/rh` -> 6. battle/mpp solo dopo
aver trovato una fonte non bloccata.
