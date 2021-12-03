from discord.ext import commands


class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def avatar(self, ctx):
        """ Prints out user avatars. 

        Syntax: .avatar <User>"""
        if len(ctx.message.content) == 7:
            await ctx.send(ctx.message.author.avatar_url)
        elif ctx.message.mentions:
            for subject in ctx.message.mentions:
                await ctx.send(subject.avatar_url)
        else:
            await ctx.send("```Syntax: .avatar <User>```")


def setup(bot):
    bot.add_cog(Avatar(bot))
