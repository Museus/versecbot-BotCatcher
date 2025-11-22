from versecbot_interface import PluginSettings, WatcherSettings


class DetectBotSettings(WatcherSettings):
    enabled: bool
    notification_channel_id: int
    channel_threshold: int
    time_threshold: int


class BotCatchersSettings(PluginSettings):
    handlers: list[DetectBotSettings]
