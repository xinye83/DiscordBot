#!/usr/bin/env python3.7

import os
import asyncio
import datetime
import random
import dotenv
import sys
import discord
from discord.ext import commands

from simc import *

dotenv.load_dotenv()

TOKEN = os.getenv('token')

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    msg = f'****** Logged in successfully as {bot.user.name} (id={bot.user.id})'
    print(msg)

@bot.command(name='test', help='For development and testing')
@commands.is_owner()
async def test(ctx, *args):
    print(len(args))
    print(args)

@bot.command(name='about', help='About this bot')
async def about(ctx):
    msg = 'Star, folk or merge me at https://github.com/xinye83/DiscordBot, or buy the author or server provider a cup of coffee!'
    await ctx.send(msg)

TIME = datetime.datetime.now()

@bot.command(name='online', help='Show bot uptime')
async def online(ctx):
    uptime = datetime.datetime.now() - TIME
    msg = f'I have been online for {str(int(uptime.total_seconds()))} seconds.'
    await ctx.send(msg)

@bot.command(name='roll', help='Simulate a dice roll', usage='sides')
@commands.guild_only()
async def roll(ctx, sides: int):
    msg = ctx.author.mention

    if sides <= 0 or sides > sys.maxsize:
        msg += ' invalid roll.'
    else:
        dice = random.choice(range(1, sides + 1))
        msg += ' rolled **' + str(dice) + '** out of **' + str(sides) + '**.'

    await ctx.send(msg)

@bot.command(name='dps', help='Simulate DPS for a character (less than 5 seconds)',
    usage='name or "simc-addon-string"')
async def dps(ctx, string: str):
    async with ctx.channel.typing():
        msg, file_name = await simc_wrapper(string, False)

    if ctx.guild is not None:
        msg = ctx.author.mention + '\n' + msg

    if os.path.exists(file_name):
        fp = open(file_name, 'rb')
        await ctx.channel.send(content=msg, file=discord.File(fp, file_name))
        fp.close()
        os.remove(file_name)
    else:
        await ctx.channel.send(content=msg)

@bot.command(name='stat', help='Simulate stat weights for a character (about 2 minutes without other load)',
    usage='name or "simc-addon-string"')
async def stat(ctx, string: str):
    async with ctx.channel.typing():
        msg, file_name = await simc_wrapper(string, True)

    if ctx.guild is not None:
        msg = ctx.author.mention + '\n' + msg

    if os.path.exists(file_name):
        fp = open(file_name, 'rb')
        await ctx.channel.send(content=msg, file=discord.File(fp, file_name))
        fp.close()
        os.remove(file_name)
    else:
        await ctx.channel.send(content=msg)

@bot.command(name='clean', help='Clean messages older than a week in a text channel')
@commands.guild_only()
@commands.is_owner()
async def clean(ctx):
    message_limit = 10000

    async with ctx.channel.typing():
        date = datetime.datetime.now() - datetime.timedelta(days=7)
        count = 0

        async for message in ctx.channel.history(limit=message_limit, before=date, oldest_first=True):
            count += 1
            await message.delete()

    await ctx.channel.send(f'_Deleted {str(count)} message(s)._')

bot.run(TOKEN)
