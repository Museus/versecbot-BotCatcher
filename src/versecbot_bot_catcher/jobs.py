from collections import defaultdict
from datetime import datetime, timedelta
from logging import getLogger

from discord import Client, Message
from versecbot_interface import Watcher

from .settings import DetectBotSettings

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
        cutoff_time = datetime.now() - timedelta(seconds=self.time_threshold)

        target_user_ids = [user_id] if user_id else list(self.data.keys())
        """Purge old entries from the data dictionary."""
        for target_user_id in target_user_ids:
            channels = self.data[target_user_id]
            for channel_id in channels.keys():
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

    def notify_channel(self, user_id: int, channel_ids: list[int]):
        """Notify notification_channel about a detected bot."""
        channel = self.client.get_channel(self.notification_channel_id)
        channel.send(
            f"User <@{user_id}> detected as bot, sent messages to {len(channel_ids)} channels within {self.time_threshold} seconds:\n"
            + ", ".join(f"<#{channel_id}>\n" for channel_id in channel_ids)
        )

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

            # message.author.timeout(
            #     duration=600,
            #     reason=f"Detected as bot by Bot Catcher plugin, sent messages to {len(self.data[message.author.id].keys())} channels within {self.time_threshold} seconds",
            # )

            for channel_id in self.data[message.author.id].keys():
                logger.info(
                    "Deleting message from user %s in channel %s",
                    message.author.id,
                    channel_id,
                )

                self.client.get_channel(channel_id).delete_messages(
                    [self.data[message.author.id][channel_id]]
                )

                logger.debug("Deleting stored data for user %s", message.author.id)
                del self.data[message.author.id]
