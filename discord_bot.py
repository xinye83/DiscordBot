#!/usr/bin/env python3.7
import os
import subprocess
import datetime
import random
import dotenv
import sys
import discord
import atexit
from discord.ext import commands

dotenv.load_dotenv()

token = os.getenv('token')

me_id = int(os.getenv('me_id'))
server_id = int(os.getenv('server_id'))

wowhead_retail_news_id = 780488984127733842

time = datetime.datetime.now()

bot = commands.Bot(command_prefix='!')

f = open('bot_command.log', 'a')

def close_log():
    f.close()

atexit.register(close_log)

async def log(ctx):
    f.write(f'{ctx.message.created_at.now()},{ctx.author},{str(ctx.channel)},{ctx.message.content}\n')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

def is_me(ctx):
    return ctx.author.id == me_id

def is_not_wowhead_retail_news(ctx):
    return ctx.author.id != wowhead_retail_news_id

def is_guild(ctx):
    return ctx.guild.id == server_id

@bot.command(name='debug', help='For debugging use only')
@commands.check(is_me)
@commands.check(is_guild)
async def debug(ctx):
    async for message in ctx.channel.history(limit=3):
        print(message)

@bot.command(name='online', help='Show bot uptime')
@commands.check(is_guild)
async def online(ctx):
    uptime = datetime.datetime.now() - time
    message = f'I have been online for {str(int(uptime.total_seconds()))} seconds.'
    await ctx.send(message)

@bot.command(name='roll', help='Simulates rolling dice')
@commands.check(is_guild)
async def roll(ctx, *args):
    await log(ctx)

    if len(args) == 0:
        sides = 100
    elif args[0].isdigit():
        sides = int(args[0])
        if sides <= 0 or sides > sys.maxsize:
            return
    else:
        return

    message = ctx.author.mention
    message += ' rolled **' + str(random.choice(range(1, sides + 1))) + '** out of **' + str(sides) + '**.'
    await ctx.send(message)

@bot.command(name='simc', help='Run a quick sim in SimulationCraft on a character in Illidan - US')
@commands.check(is_guild)
async def simc(ctx, *args):
    await log(ctx)

    # can only run in text channel 'misc'
    if str(ctx.channel) != "misc":
        return

    if len(args) != 1:
        return

    name = str(args[0]).title()

    file_name = name + ".html"

    simc = "/home/xye/simc/engine/simc"

    cmd = simc + " armory=us,illidan," + name.lower()
    cmd += " calculate_scale_factors=0 threads=1 process_priority=low html=" + file_name

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    stdout, stderr = p.communicate()
    retcode = p.wait()

    if retcode:
        print('****** simc returned error code ' + str(retcode))
        print('****** stdout\n' + stdout.decode("utf-8"))
        print('****** stderr\n' + stderr.decode("utf-8"))
        return

    output = stdout.decode("utf-8")

    i1 = output.find('DPS=', 0, len(output)) + 4
    i2 = output.find('.', i1, len(output)) + 3

    dps = output[i1:i2]

    i1 = output.find('Player:', 0, len(output)) + len('Player: ') + len(name) + 1
    i1 = output.find(' ', i1, len(output)) + 1
    i2 = output.find(' ', i1, len(output))

    class_ = output[i1:i2]
    if class_ == 'demonhunter':
        class_ = 'demon hunter'
    class_ = class_.title()

    i1 = i2 + 1
    i2 = output.find(" ", i1, len(output))

    spec = output[i1:i2]
    if spec == 'beast_mastery':
        spec = 'beast mastery'
    spec = spec.title()

    i1 = output.find('SimulationCraft', 0, len(output)) + len('SimulationCraft ')
    i2 = output.find(' ', i1, len(output))
    simc_ver = output[i1:i2]

    i1 = output.find('World of Warcraft', 0, len(output)) + len('World of Warcraft ')
    i2 = output.find(' ', i1, len(output))
    wow_ver = output[i1:i2]

    message = ctx.author.mention + '\n'
    message += '**Character:** ' + name + ' - Illidan\n'
    message += '**Spec & Class:** ' + spec + ' ' + class_ + '\n'
    message += '**DPS:** ' + dps + '\n'
    message += '_' + output.partition('\n')[0] + '_'

    fp = open(file_name, 'rb')
    await ctx.channel.send(content=message, file=discord.File(fp, file_name))
    fp.close()

    os.remove(file_name)

@bot.command(name='clear', help='Clean messages older than a week')
@commands.check(is_me)
@commands.check(is_guild)
async def clear(ctx):
    await log(ctx)

    date = datetime.datetime.now() - datetime.timedelta(days=7)
    deleted = await ctx.channel.purge(limit=10000, before=date, oldest_first=True, bulk=False)

    if str(ctx.channel) == 'wowhead':
        await ctx.channel.purge(limit=10000, check=is_not_wowhead_retail_news)
    else:
        await ctx.channel.send('_Deleted {} message(s)_'.format(len(deleted)))

bot.run(token)
