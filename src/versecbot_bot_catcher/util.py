import discord


def create_embed(message: discord.Message) -> discord.Embed:
    message_embed = discord.Embed(
        description=message.content, timestamp=message.created_at
    )

    message_embed.set_author(
        name=message.author.display_name, icon_url=message.author.display_avatar.url
    )

    message_embed.set_footer(text=f"Sent in <#{message.channel.id}>")

    return message_embed
