# Aristotle

A Telegram bot for [eRepublik](https://www.erepublik.com), the browser-based nation simulation game.

Aristotle brings the features of the Discord bot [Socrates](https://github.com/Curlybear/Socrates)
to Telegram, so players can look things up without leaving their chat.

**Try it now: [@aristotle_erep_bot](https://t.me/aristotle_erep_bot)**

## What it can do

- **Citizen profiles**: look up any player by name or ID, with their avatar.
- **Market**: find the best offers for food, weapons, tickets, houses, aircraft and raw materials.
- **Jobs**: browse the best job offers, worldwide or by country.
- **War**: occupied regions, air rounds, epic battles and combat orders.
- **Diplomacy**: a country's mutual protection pacts (MPPs).
- **Tools**: convert between eRepublik days and calendar dates.

Type `/help` in the chat to see every command.

## Getting started

You need Python 3.11+, a Telegram bot token from [@BotFather](https://t.me/BotFather) and an
[erepublik.tools](https://erepublik.tools/en) API key.

```bash
pip install -e .
cp .env.example .env    # add your token and API key
python -m aristotle
```

A Docker setup is also included. For configuration, architecture and deployment details, see the
[developer notes](docs/sviluppo.md).

## Credits and license

Game data comes from [erepublik.tools](https://erepublik.tools/en) and from erepublik.com.

Aristotle is derived from Socrates by Curlybear and is released under the
[GPL-3.0](LICENSE), the same license.
