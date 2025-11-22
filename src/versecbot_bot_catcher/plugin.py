from logging import getLogger

from discord import Intents
from versecbot_interface import Plugin

from .jobs import DetectBots
from .settings import BotCatchersSettings, DetectBotSettings


logger = getLogger("discord").getChild("versecbot.plugins.bot_catcher")


class BotCatcherPlugin(Plugin):
    name: str = "bot_catcher"
    intents = [Intents.guild_messages]

    def __init__(self):
        super().__init__()

    def initialize(self, settings: BotCatchersSettings, client):
        logger.info(
            "Initializing Bot Catcher plugin...",
        )

        # Register Bot Catcher jobs
        for handler_settings_raw in settings.handlers:
            handler_settings = DetectBotSettings.model_validate(handler_settings_raw)
            try:
                bot_catcher = DetectBots(client, handler_settings)
                bot_catcher.initialize(handler_settings, client)
            except Exception:
                logger.exception(
                    "Failed to initialize Bot Catcher",
                    ", ".join(
                        str(channel_id) for channel_id in handler_settings.channel_ids
                    ),
                )
            else:
                self.assign_job(bot_catcher)
                logger.info("Watching for bots in all channels")

        logger.debug("Bot Catcher initialized")
