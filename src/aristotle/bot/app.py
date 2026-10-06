from __future__ import annotations

from telegram import BotCommand
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from ..config import Settings
from ..core.battles import BattleService
from ..core.client import ErepToolsClient
from ..core.market import MARKET_ITEMS, MarketService
from ..core.mpp import MppService
from ..core.regions import RegionService
from ..core.services import CitizenService
from ..core.site import ErepSiteClient
from .errors import on_error
from .handlers import basic, market, meta, region, user, war
from .keyboards import USER_PICK_PREFIX

COMMANDS = [
    BotCommand("user", "Scheda cittadino (id o nome)"),
    *[
        BotCommand(i.command, f"Migliori offerte: {i.title}" + ("" if i.fixed_quality else " <q>"))
        for i in MARKET_ITEMS
    ],
    BotCommand("sh", "Round aerei in arrivo / a basso danno"),
    BotCommand("epic", "Battaglie epic e full-scale"),
    BotCommand("co", "Combat order attivi"),
    BotCommand("mpp", "MPP di un paese"),
    BotCommand("mppsraw", "CSV di tutti gli MPP"),
    BotCommand("rh", "Regioni occupate di un paese"),
    BotCommand("jobs", "Migliori offerte di lavoro [paese]"),
    BotCommand("convert", "Converte eRepublik day <-> data"),
    BotCommand("ping", "Verifica che il bot risponda"),
    BotCommand("help", "Aiuto"),
]


def build_application(settings: Settings) -> Application:
    async def post_init(app: Application) -> None:
        client = ErepToolsClient(
            api_key=settings.erep_api_key.get_secret_value(),
            base_url=settings.erep_api_base,
            version=settings.erep_api_version,
            search_version=settings.erep_search_version,
            cache_ttl=settings.cache_ttl,
        )
        app.bot_data["client"] = client
        app.bot_data["citizen_service"] = CitizenService(client)
        app.bot_data["market_service"] = MarketService(client)
        app.bot_data["region_service"] = RegionService(client)
        site = ErepSiteClient()
        app.bot_data["site"] = site
        app.bot_data["battle_service"] = BattleService(site)
        app.bot_data["mpp_service"] = MppService(site)
        await app.bot.set_my_commands(COMMANDS)

    async def post_shutdown(app: Application) -> None:
        await app.bot_data["client"].aclose()
        await app.bot_data["site"].aclose()

    app = (
        Application.builder()
        .token(settings.telegram_token.get_secret_value())
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.bot_data["settings"] = settings

    app.add_handler(CommandHandler("start", basic.start))
    app.add_handler(CommandHandler("help", basic.help_command))
    app.add_handler(CommandHandler("user", user.user_command))
    app.add_handler(CommandHandler("jobs", market.jobs_command))
    app.add_handler(CommandHandler("rh", region.rh_command))
    for name, fn in (
        ("sh", war.sh_command),
        ("epic", war.epic_command),
        ("co", war.co_command),
        ("mpp", war.mpp_command),
        ("mppsraw", war.mppsraw_command),
    ):
        app.add_handler(CommandHandler(name, fn))
    app.add_handler(CommandHandler("convert", meta.convert_command))
    app.add_handler(CommandHandler("ping", meta.ping))
    for item in MARKET_ITEMS:
        app.add_handler(CommandHandler(item.command, market.make_market_handler(item)))
    app.add_handler(CallbackQueryHandler(user.user_pick, pattern=f"^{USER_PICK_PREFIX}\\d+$"))
    app.add_error_handler(on_error)
    return app
