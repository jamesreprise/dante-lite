import discord
import aiohttp
import requests
import calendar
import random
import toml
from datetime import datetime, timedelta
from discord.ext import commands, tasks


class NowPlaying(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.spotify_icon = "https://primetime.james.gg/images/spotify.png"

    def addressor(self, user):
        return (user.nick if user.nick else user.name)

    @commands.command()
    async def np(self, ctx):
        """ Displays what the user is currently listening to.

        Syntax: .np <User> """

        for subject in ctx.message.mentions:
            await ctx.send(embed=await self.spotify_embed(subject))
        else:
            await ctx.send(embed=await self.spotify_embed(ctx.message.author))
    
    async def spotify_embed(self, member):
        found = False
        for activity in member.activities:
            if isinstance(activity, discord.Spotify):
                spotify = activity
                found = True
                addressor = self.addressor(member)
                embed = discord.Embed(title=f"{addressor} is listening to {spotify.artists[0]}", colour=spotify.color)
                embed.add_field(name = "Song", value = f"[{spotify.title}](https://open.spotify.com/track/{spotify.track_id})")
                embed.add_field(name="Album", value=f"{spotify.album}", inline=False)
                embed.set_image(url=spotify.album_cover_url)
                embed.set_footer(text=f"via Spotify.", icon_url=self.spotify_icon)
                return embed
        if not found:
            addressor = self.addressor(member)
            embed = discord.Embed(title=f"{addressor} isn't listening to anything.", colour=0xC3000D)
            embed.set_footer(text=f"via Spotify.", icon_url=self.spotify_icon)
            return embed

def setup(bot):
    bot.add_cog(NowPlaying(bot))
