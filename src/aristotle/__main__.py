from __future__ import annotations

import logging

from .bot.app import build_application
from .config import Settings


def main() -> None:
    settings = Settings()  # type: ignore[call-arg]
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    # httpx logga l'URL completo a INFO: contiene la API key come query param.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    build_application(settings).run_polling()


if __name__ == "__main__":
    main()
