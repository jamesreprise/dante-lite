#./usr/bin/env python3
import discord
import toml
from discord.ext import commands
from datetime import datetime, timedelta, timezone

class Dante(commands.Bot):
    def __init__(self, config):
        self.config = config
        super().__init__(command_prefix = self.prefix, owner_id = config['ids']['owner'], intents=discord.Intents().all())
        self.token = self.config['keys']['discord_bot_token']
        self.prefixes = {}
        self.silent_guilds = []
        self.max_messages = 10_000
    
    def time_now(self):
        return datetime.utcnow().replace(microsecond=0, tzinfo=timezone.utc).isoformat()
 
    def prefix(self, bot, message):
        if not message.guild:
            return "."
        else:
            return self.prefixes.get(message.guild.id, ".")

config = toml.load("config.toml")
bot = Dante(config)

bot.load_extension("cogs.ping")
bot.load_extension("cogs.admin")
bot.load_extension("cogs.avatar")
bot.load_extension("cogs.metacog")
bot.load_extension("cogs.wolfram")
bot.load_extension("cogs.nowplaying")
bot.load_extension("cogs.autodelete")
bot.load_extension("cogs.panopticon")
bot.load_extension("cogs.errorhandler")

# Global check on every command.
@bot.check
def exclude_silent_guilds(ctx):
    if not ctx.guild:
        return True
    else:
        return (not ctx.guild.id in ctx.bot.silent_guilds) or (ctx.author.id == ctx.bot.owner_id)

@bot.event
async def on_ready():
    print(f"[{bot.time_now()}] Ready. Logged in as {bot.user}.")
    server_list = [guild.name for guild in bot.guilds]
    print(f"[{bot.time_now()}] Present on {len(server_list)} servers: {server_list}.")
    # await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Streaming(name="", url=""))
     
bot.run(bot.token)