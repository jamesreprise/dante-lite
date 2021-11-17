import discord
import aiohttp
import requests
import calendar
import random
import toml
from datetime import datetime, timedelta
from discord.ext import commands, tasks

class User(): 
    def __init__(self, name, snowflake, count, month_delta):
        self.name = name
        self.snowflake = snowflake
        self.count = int(count)
        self.month_delta = int(month_delta)

class LastFM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.LASTFM_LIMIT = 200
        self.connection = psycopg2.connect("dbname=content user=content")
        self.cursor = self.connection.cursor()
        self.playcount_cache = self.get_playcounts()
        self.username_cache = self.get_dict()
        self.session = aiohttp.ClientSession()
        self.spotify_icon = "https://primetime.james.gg/images/spotify.png"
        self.lastfm_icon = "https://primetime.james.gg/images/lastfm.png"
        self.last_fm_api_key = self.bot.config['keys']['last_fm_api_key']
        self.lastfm_url_pattern = "https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={user}&api_key=" + self.last_fm_api_key + "&limit=" + str(self.LASTFM_LIMIT) + "&format=json"
        self.lastfm_info_url_pattern = "https://ws.audioscrobbler.com/2.0/?method=user.getinfo&user={user}&api_key=" + self.last_fm_api_key + "&format=json"
        self.kurt_week_influx_url_pattern = "http://stats.kurt.gg/api/datasources/proxy/5/query?db=lastfm&q=SELECT%20%22{}%22%20from%20%22delta-7day-clean%22%20order%20by%20time%20desc%20limit%201&epoch=ms"
        self.kurt_4week_influx_url_pattern = "http://stats.kurt.gg/api/datasources/proxy/5/query?db=lastfm&q=SELECT%20%22{}%22%20from%20%22delta-28day-clean%22%20order%20by%20time%20desc%20limit%201&epoch=ms"
        self.update_playcount_cache.start()


    @commands.command()
    async def streak(self, ctx):
        """ Gets the user's listen streak for a song.

        Syntax: .streak [User]"""
        if ctx.message.mentions:
            for mention in ctx.message.mentions:
                if mention.id in self.username_cache:
                    await ctx.send(embed=await self.lastfm_embed(mention))
                else:
                    await ctx.send(embed=self.register_embed(self.addressor(mention)))
        elif ctx.author.id in self.username_cache:
            await ctx.send(embed=await self.lastfm_embed(ctx.author))
        else:
            await ctx.send(embed=self.register_embed(self.addressor(ctx.author)))


    @commands.command()
    async def crossover(self, ctx):
        """ Finds when 2 users will cross playcounts.

        Syntax: .crossover <User> <User> """

        mentions = ctx.message.mentions
        if len(mentions) == 2:

            users = []
            for mention in mentions:
                name = self.addressor(mention)
                snowflake = mention.id
                count = await self.get_playcount(snowflake)
                month_delta = await self.get_4week_delta(self.username_cache[mention.id])
                users.append(User(name, snowflake, count, month_delta))
            overtaker = users[0] if users[0].month_delta > users[1].month_delta else users[1]
            undertaker = users[0] if overtaker == users[1] else users[1]
            count_difference = undertaker.count - overtaker.count
            if count_difference == 0:
                await ctx.send(embed=self.create_crossover_embed(overtaker, undertaker, "You're neck and neck!"))
            elif count_difference < 0:
                await ctx.send(embed=self.create_crossover_embed(undertaker, overtaker, "At current rates, {} will never catch up with {}!".format(undertaker.name, overtaker.name)))
            else:
                delta_difference = overtaker.month_delta - undertaker.month_delta
                month_count = (count_difference / delta_difference)
                overtake_time = datetime.now() + timedelta(weeks=month_count * 4)
                overtake_count = overtaker.count + \
                    (month_count * overtaker.month_delta)

                await ctx.send(embed=self.create_crossover_embed(overtaker, undertaker, self.date_to_string(overtake_time), count=overtake_count))
        else:
            await ctx.send("Syntax: .crossover <User> <User>")

    @commands.command()
    async def np(self, ctx):
        """ Displays what the user is currently listening to.

        Syntax: .np <User> """

        if ctx.message.mentions:
            for subject in ctx.message.mentions:
                await ctx.send(embed=await self.music_embed(subject))
        elif len(ctx.message.content.split(" ")) == 1:
            await ctx.send(embed=await self.music_embed(ctx.message.author))
        else:
            if len(ctx.message.content.split(" ")) > 1:
                async with self.session.get(self.lastfm_info_url_pattern.format(user=ctx.message.content.split(" ")[1])) as t:
                    last_fm_icon_json = await t.json()
                if 'message' not in last_fm_icon_json:
                    self.username_cache[ctx.message.author.id] = last_fm_icon_json['user']['name']
                    self.write_dict(ctx.message.author.id, self.username_cache[ctx.message.author.id])
                    embed = discord.Embed(
                        title="Registration", colour=0XC3000D)
                    embed.add_field(name="Response", value="{}'s last.fm username set to {}.".format(
                        ctx.message.author.name, last_fm_icon_json['user']['name']))
                    embed.set_thumbnail(
                        url=last_fm_icon_json['user']['image'][2]['#text'])
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="Registration", colour=0XC3000D)
                    embed.add_field(name="Response", value="I wasn't able to find user {} at {}.".format(
                        ctx.message.content.split(" ")[1], "https://last.fm/user/" + ctx.message.content.split(" ")[1]))
                    await ctx.send(embed=embed)

    @commands.command()
    async def count(self, ctx):
        """ Displays last.fm information about a user. 

        Syntax: .count <User>"""

        if len(ctx.message.content.split(" ")) == 1:
            if ctx.message.author.id not in self.username_cache:
                embed = discord.Embed(title="Registration", colour=0XC3000D)
                embed.add_field(
                    name="Instruction", value="Usage: .np [last.fm username], then just .np after (you're seeing this because you have no set username.)")
                await ctx.send(embed=embed)
            else:
                async with self.session.get(self.lastfm_info_url_pattern.format(user=self.username_cache[ctx.message.author.id])) as s:
                    last_fm_icon_json = await s.json()
                embed = await self.count_embed(last_fm_icon_json, ctx.message.author)
                await ctx.send(embed=embed)
        else:
            if ctx.message.mentions:
                for subject in ctx.message.mentions:
                    if subject.id in self.username_cache:
                        async with self.session.get(self.lastfm_info_url_pattern.format(user=self.username_cache[subject.id])) as s:
                            last_fm_icon_json = await s.json()
                        embed = await self.count_embed(last_fm_icon_json, subject)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("```{} hasn't registered their last.fm username.```".format(self.addressor(subject)))

    def write_dict(self, discord_id, username):
        self.cursor.execute("UPDATE lastfm SET username = %s WHERE discord_id = %s;", (username, discord_id))
        self.connection.commit()

    def get_dict(self):
        self.cursor.execute("SELECT discord_id, username FROM lastfm;")
        users = self.cursor.fetchall()

        user_dict = {}
        for user in users:
            user_dict[user[0]] = user[1]

        return user_dict

    def addressor(self, user):
        return (user.nick if user.nick else user.name)

    def date_to_string(self, date_time):
        day_ordinal = "th" if 4 <= date_time.day <= 20 else {
            1: "st", 2: "nd", 3: "rd"}.get(date_time.day % 10, "th")
        hour_string = "12am" if date_time.hour == 0 else str(
            date_time.hour) + "am" if date_time.hour / 12 < 1 else str(date_time.hour % 12) + "pm" if date_time.hour != 24 else "12pm"
        time_string = hour_string + " on " + calendar.day_name[date_time.weekday()] + ", the " + str(
            date_time.day) + day_ordinal + " of " + calendar.month_name[date_time.month] + ", " + str(date_time.year)
        return time_string

    def register_embed(self, name):
        embed = discord.Embed(title=name + " hasn't registered.", colour=0XC3000D)
        embed.add_field(
            name="Instruction", value="Usage: .np [last.fm username], then just .np after (you're seeing this because you have no set username.)")
        return embed

    def create_crossover_embed(self, overtaker, undertaker, time_string, count=0):
        embed = discord.Embed(title="When will {} overtake {}?".format(
            overtaker.name, undertaker.name), colour=0XC3000D)
        embed.add_field(name="Date & Time",
                        value=time_string + ".", inline=False)
        if count != 0:
            embed.add_field(name="Count", value="{} scrobbles.".format(
                int(count)), inline=False)
        embed.add_field(name="Listen Rates", value="{}: {} + {} per 4 weeks, {}: {} + {} per 4 weeks".format(undertaker.name,
                undertaker.count, undertaker.month_delta, overtaker.name, overtaker.count, overtaker.month_delta), inline=False)
        return embed
    
    def get_playcounts(self):
        self.cursor.execute("SELECT discord_id, playcount FROM lastfm;")
        users = self.cursor.fetchall()

        playcount_dict = {}
        for user in users:
            playcount_dict[user[0]] = user[1]

        return playcount_dict
    
    def set_playcount(self, discord_id, playcount):
        self.playcount_cache[discord_id] = playcount
        self.cursor.execute("UPDATE lastfm SET playcount = %s WHERE discord_id = %s;", (playcount, discord_id))
        self.connection.commit()

    async def get_week_delta(self, lastfm_username):
        async with self.session.get(self.kurt_week_influx_url_pattern.format(lastfm_username)) as r:
            week_delta_json = await r.json()
        return week_delta_json['results'][0]['series'][0]['values'][0][1]

    async def get_4week_delta(self, lastfm_username):
        async with self.session.get(self.kurt_4week_influx_url_pattern.format(lastfm_username)) as r:
            fourweek_delta_json = await r.json()
        return fourweek_delta_json['results'][0]['series'][0]['values'][0][1]


    async def get_playcount(self, member_id):
        lastfm_dict = self.get_dict()
        async with self.session.get(self.lastfm_info_url_pattern.format(user=lastfm_dict[member_id])) as s:
            last_fm_icon_json = await s.json()
        self.set_playcount(member_id, last_fm_icon_json['user']['playcount'])
        return self.playcount_cache[member_id]

    async def music_embed(self, member):
        for activity in member.activities:
            if isinstance(activity, discord.Spotify):
                embed = await self.spotify_embed(member, activity)
                return embed
        if member.id not in self.username_cache:
            embed = await self.register_embed(self.addressor(member))
            return embed
        else:
            embed = await self.lastfm_embed(member)
            return embed

    async def spotify_embed(self, member, spotify):
        addressor = self.addressor(member)
        embed = discord.Embed(title="{} is listening to {}".format(
            addressor, spotify.artists[0]), colour=spotify.color)
        embed.add_field(name = "Song", value = "[{}](https://open.spotify.com/track/{})".format(spotify.title, spotify.track_id))
        embed.add_field(name="Album", value="{}".format(
            spotify.album), inline=False)
        embed.set_image(url=spotify.album_cover_url)
        if member.id in self.username_cache:
            embed.set_footer(text=f"via Spotify. Total tracks played: {self.playcount_cache[member.id]}.",
                        icon_url=self.spotify_icon)
        return embed

    async def lastfm_embed(self, member):
        addressor = self.addressor(member)
        lastfm_dict = self.username_cache

        async with self.session.get(self.lastfm_url_pattern.format(user=lastfm_dict[member.id])) as r:
            last_fm_response_json = await r.json()
        async with self.session.get(self.lastfm_info_url_pattern.format(user=lastfm_dict[member.id])) as s:
            last_fm_icon_json = await s.json()

        self.set_playcount(member.id, last_fm_icon_json['user']['playcount'])

        if 'recenttracks' in last_fm_response_json:

            streak_track = last_fm_response_json['recenttracks']['track'][0]['mbid']
            streak_count = 0
            
            while streak_count < self.LASTFM_LIMIT and streak_track == last_fm_response_json['recenttracks']['track'][streak_count]['mbid']:
                streak_count += 1
            
            
            liveNow = "is currently" if '@attr' in last_fm_response_json[
                'recenttracks']['track'][0] else "was"
            embed = discord.Embed(title="{} {} listening to {}".format(
                addressor, liveNow, last_fm_response_json['recenttracks']['track'][0]['artist']['#text']), colour=0XC3000D)
            if last_fm_response_json['recenttracks']['track'][0]['image'][3]['#text'] != "https://lastfm-img2.akamaized.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.png":
                embed.set_image(
                    url=last_fm_response_json['recenttracks']['track'][0]['image'][3]['#text'])
            embed.add_field(name="Song", value="{}".format(
                last_fm_response_json['recenttracks']['track'][0]['name']))
            self.playcount_cache[member.id] = last_fm_icon_json['user']['playcount']
            embed.add_field(
                name="Album", value=last_fm_response_json['recenttracks']['track'][0]['album']['#text'], inline=False)
            embed.set_footer(text="{} via last.fm. Total tracks played: {}.".format(
                lastfm_dict[member.id], last_fm_icon_json['user']['playcount']), icon_url=last_fm_icon_json['user']['image'][2]['#text'])
            
            if streak_count > 3 and streak_count < self.LASTFM_LIMIT:
                embed.add_field(name="Streak Count", value=str(streak_count) + "x", inline=False)
            elif streak_count == self.LASTFM_LIMIT:
                embed.add_field(name="Streak Count", value= str(self.LASTFM_LIMIT) + "x (MAX)", inline=False)
            return embed
        embed = discord.Embed(title="last.fm seems down from here.",
                              description="A U.S. secret court order has been issued to deploy a SWAT team to your house in light of this error. Please stay seated. Do not attempt to leave your domicile. Remember: Hands up, don't shoot!")
        return embed

    async def count_embed(self, info_json, member):
        embed = discord.Embed(title="{} on last.fm".format(
            self.username_cache[member.id]), colour=0XC3000D)

        if int(info_json['user']['playcount']) > 0:
            playcount = info_json['user']['playcount']
            self.playcount_cache[member.id] = info_json['user']['playcount']
        elif member.id in self.playcount_cache:
            playcount = self.playcount_cache[member.id]
        else:
            playcount = "Not Found"

        embed.add_field(name="Total Scrobbles", value="{}".format(playcount))
        embed.add_field(name="Scrobbles This Week", value=await self.get_week_delta(self.username_cache[member.id]))
        embed.add_field(name="Profile", value="{}".format(
            info_json['user']['url']), inline=False)

        embed.set_thumbnail(url=info_json['user']['image'][2]['#text'])
        unixtime_registered = int(info_json['user']['registered']['unixtime'])
        embed.set_footer(text="Registered {}.".format(datetime.fromtimestamp(
            unixtime_registered).year), icon_url=self.lastfm_icon)
        return embed
    
    @tasks.loop(minutes = 30.0)
    async def update_playcount_cache(self):
        lastfm_dict = self.get_dict()
        for k in lastfm_dict.keys():
            await self.get_playcount(k)


def setup(bot):
    bot.add_cog(LastFM(bot))
