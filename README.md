# VerSecBot - Bot Catcher

This plugin instructs VerSecBot to watch for an account posting in multiple channels in a short period of time, time them out, and notify the moderator team.

To use it, install the package and add the following block to your configuration, replacing values in <> with your desired values:

```
    [versecbot.plugins.bot_catcher]
        enabled = true

    [[versecbot.plugins.bot_catcher.handlers]]
        enabled = true
        channel_threshold = <number of channels>
        time_threshold = <seconds to count channels>
```
