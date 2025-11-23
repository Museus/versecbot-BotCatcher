from collections import defaultdict
from datetime import datetime, timedelta, timezone
from logging import getLogger

from discord import Client, Message
from versecbot_interface import Watcher

from .settings import DetectBotSettings
from .util import create_embed

logger = getLogger("discord").getChild("versecbot.plugins.bot_catcher.detect_bots")


class DetectBots(Watcher):
    client: Client
    name: str

    def __init__(self, client: Client, settings: DetectBotSettings):
        super().__init__(settings)
        self.client = client
        self.channel_threshold = settings.channel_threshold
        self.time_threshold = settings.time_threshold
        self.notification_channel_id = settings.notification_channel_id
        self.data = defaultdict(dict)
        self.name = "watcher_detect_bots"

    def initialize(self, settings: DetectBotSettings, *args):
        """Nothing special to do here."""
        logger.debug("Initializing...")
        super().initialize(settings, *args)

    def log_message(self, message: Message):
        logger.debug(
            "[%s] Received message from %s <%s>",
            message.id,
            message.author.name,
            message.author.id,
        )
        self.data[message.author.id][message.channel.id] = message

    def purge_old_entries(self, user_id: int = None):
        cutoff_time = datetime.now(tz=timezone.utc) - timedelta(
            seconds=self.time_threshold
        )

        target_user_ids = [user_id] if user_id else list(self.data.keys())
        """Purge old entries from the data dictionary."""
        for target_user_id in target_user_ids:
            channels = self.data[target_user_id]
            for channel_id in list(channels.keys()):
                message: Message = channels[channel_id]
                if message.created_at < cutoff_time:
                    logger.debug(
                        "Purging old entry for user %s in channel %s",
                        target_user_id,
                        channel_id,
                    )
                    del channels[channel_id]

            if not channels:
                del self.data[user_id]

    def is_user_above_threshold(self, user_id: int) -> bool:
        """Check if a user has sent messages in more than the allowed number of channels."""
        if user_id not in self.data:
            return False

        # Purge any old entries for user first
        self.purge_old_entries(user_id)

        # Check how many channels they have messages in
        channel_count = len(self.data[user_id].keys())

        return channel_count >= self.channel_threshold

    async def notify_channel(self, user_id: int, messages: list[int]):
        """Notify notification_channel about a detected bot."""
        channel = self.client.get_channel(self.notification_channel_id)
        embeds = [create_embed(msg) for msg in messages]
        notification_message = f"User <@{user_id}> detected as bot, sent messages to {len(messages)} channels within {self.time_threshold} seconds"
        return await channel.send(notification_message, embeds=embeds)

    def should_act(self, message: Message) -> bool:
        if not super().should_act(message):
            return False

        return True

    async def act(self, message: Message):
        logger.info(
            "Handling message %s from %s <%s>",
            message.id,
            message.author.name,
            message.author.id,
        )

        self.log_message(message)

        if self.is_user_above_threshold(message.author.id):
            logger.info(
                "User %s <%s> exceeded thresholds with %d channels within %d seconds",
                message.author.name,
                message.author.id,
                len(self.data[message.author.id].keys()),
                self.time_threshold,
            )

            await self.notify_channel(
                message.author.id, list(self.data[message.author.id].values())
            )

            message.author.timeout(
                until=datetime.now(tz=timezone.utc) + timedelta(minutes=10),
                reason="Detected as bot by Bot Catcher plugin",
            )

            for channel_id in list(self.data[message.author.id].keys()):
                logger.info(
                    "Deleting message %s from %s <%s> in channel %s",
                    message.id,
                    message.author.name,
                    message.author.id,
                    message.channel.id,
                )

                last_message = self.data[message.author.id].get(channel_id)
                if last_message:
                    await self.client.get_channel(channel_id).delete_messages(
                        [last_message]
                    )

            logger.debug("Deleting stored data for user %s", message.author.id)
            del self.data[message.author.id]
