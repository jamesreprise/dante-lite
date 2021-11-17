from discord.ext import commands
import requests
import discord

class Wolfram(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wolframKey = self.bot.config['keys']['wolfram_token']
        self.wolframURL = "https://api.wolframalpha.com/v1/result?i={}&appid={}"
        self.wolframIconURL = "https://primetime.james.gg/images/wolframalpha.png"

    @commands.command()
    async def wa(self, ctx):
        """ Short answers provided by WolframAlpha.

        Syntax: .wa <query>"""
        embed = discord.Embed(description=requests.get(self.wolframURL.format(ctx.message.content[4::], self.wolframKey)).content.decode("utf-8"), colour=0XFF3413)
        embed.set_author(name="Reponse to query: \"" + ctx.message.content[4::] + "\"")
        embed.set_footer(text="WolframAlpha", icon_url=self.wolframIconURL)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Wolfram(bot))

