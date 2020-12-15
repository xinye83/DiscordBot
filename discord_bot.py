#!/usr/bin/env python3.7
import os
import asyncio
import datetime
import random
import dotenv
import sys
import discord
from discord.ext import commands

dotenv.load_dotenv()

token = os.getenv('token')

wowhead_retail_news_id = 780488984127733842
raiderio_id = 780543054204764191
general_id = 780487470873182239

time = datetime.datetime.now()

bot = commands.Bot(command_prefix='!')

async def log(ctx):
    commend = f'echo "{ctx.message.created_at.now()},{ctx.author},{str(ctx.channel)},{ctx.message.content}" >> bot_command.log'
    os.system(commend)

@bot.event
async def on_ready():
    print('\n\n******')
    print(f'****** Logged in successfully as {bot.user.name} (id={bot.user.id})')

async def is_me(ctx):
    return await bot.is_owner(ctx.author)

async def is_general(ctx):
    return ctx.channel.id == general_id

@bot.command(name='test')
@commands.check(is_me)
async def test(ctx, *args):
    print(len(args))
    print(args)

@bot.command(name='about', help='About this bot')
@commands.check(is_general)
async def about(ctx):
    message = 'Star, folk or merge me at https://github.com/xinye83/DiscordBot, or buy the author or server provider a cup of coffee!'
    await ctx.send(message)

@bot.command(name='online', help='Show bot uptime')
@commands.check(is_general)
async def online(ctx):
    await log(ctx)

    uptime = datetime.datetime.now() - time
    message = f'I have been online for {str(int(uptime.total_seconds()))} seconds.'
    await ctx.send(message)

@bot.command(name='roll', help='Simulate a dice roll')
@commands.check(is_general)
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

async def simc_(name, stat=False):
    simc = '/home/xye/simc/engine/simc'
    file_name = name.title() + '.html'

    if os.path.exists(file_name):
        os.remove(file_name)

    cmd = simc + ' armory=us,illidan,' + name.lower()
    cmd += ' calculate_scale_factors='
    if stat:
        cmd += '1'
    else:
        cmd += '0'
    cmd += ' threads=1 html=' + file_name

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    await proc.wait()

    stdout, stderr = await proc.communicate()

    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")

    if proc.returncode:
        print('\n****** simc returned error code ' + str(proc.returncode))
        print('****** stdout\n' + stdout)
        print('****** stderr\n' + stderr)

    return proc.returncode, stdout, stderr

def get_dps(string):
    i1 = string.find('DPS=', 0, len(string)) + 4
    i2 = string.find('.', i1, len(string)) + 3
    dps = string[i1:i2]
    return dps

def get_class_spec(string):
    i1 = string.find('Player:', 0, len(string)) + len('Player:') + 1
    i1 = string.find(' ', i1, len(string)) + 1
    i1 = string.find(' ', i1, len(string)) + 1
    i2 = string.find(' ', i1, len(string))
    class_ = string[i1:i2]

    if class_ == 'demonhunter':
        class_ = 'demon hunter'

    class_ = class_.title()

    i1 = i2 + 1
    i2 = string.find(' ', i1, len(string))
    spec = string[i1:i2]

    if spec == 'beast_mastery':
        spec = 'beast mastery'

    spec = spec.title()

    return class_, spec

def get_simc_ver(string):
    return '_' + string.partition('\n')[0] + '_'

@bot.command(name='simc', help='**Deprecated**')
@commands.check(is_general)
async def simc(ctx):
    await ctx.channel.send(ctx.author.mention + ' `!simc` is deprecated, please use `!dps` or `!stat` instead.')

@bot.command(name='dps', help='Simulate DPS for character in US-Illidan (less than 5 seconds)')
@commands.check(is_general)
async def dps(ctx, *args):
    await log(ctx)

    if len(args) != 1:
        return

    name = str(args[0]).title()
    file_name = name + '.html'

    async with ctx.channel.typing():
        retcode, stdout, stderr = await simc_(name)

    if retcode:
        await ctx.channel.send(ctx.author.mention + ' something went wrong with simc.')
        return

    dps = get_dps(stdout)
    class_, spec = get_class_spec(stdout)

    message = ctx.author.mention + '\n'
    message += f'**Character:** {name}, {spec} {class_}\n'
    message += f'**DPS:** {dps}\n'
    message += get_simc_ver(stdout)

    fp = open(file_name, 'rb')
    await ctx.channel.send(content=message, file=discord.File(fp, file_name))
    fp.close()

    os.remove(file_name)

def get_scale(string, name):
    i1 = string.find('Scale Factors:\n  ' + name, 0, len(string))
    i1 += len('Scale Factors:\n  ' + name)
    i2 = string.find('\n', i1, len(string))
    scale = string[i1:i2].strip().split('  ')

    w1 = 0
    w2 = 0
    w3 = 0

    table = []
    for item in scale:
        i1 = item.find('=', 0, len(item))
        i2 = item.find('(', i1, len(item))
        i3 = item.find(')', i2, len(item))

        w1 = max(w1, i1)
        w2 = max(w2, i2 - i1 - 1)
        w3 = max(w3, i3 - i2 - 1)

        table.append([item[0: i1], item[i1 + 1: i2], item[i2 + 1: i3]])

    w1 = max(w1, len('Stat'))
    w2 = max(w2, len('Scale'))
    w3 = max(w3, len('Error'))

    temp = '+-' + '-' * w1 + '-+-' + '-' * w2 + '-+-' + '-' * w3 + '-+\n'

    message = '```\n' + temp
    message += '| Stat' + ' ' * (w1 - len('Stat')) + ' | Scale' + ' ' * (w2 - len('Scale')) + ' | Error' + ' ' * (w3 - len('Error')) + ' |\n'
    message += temp
    for factor, score, error in table:
        message += '| ' + factor + ' ' * (w1 - len(factor)) + ' | ' + score + ' ' * (w2 - len(score)) + ' | ' + error + ' ' * (w3 - len(error)) + ' |\n'

    message += temp
    message += '```'

    return message

@bot.command(name='stat', help='Simulate stat weights for a character in US-Illidan (about 3 minutes)')
@commands.check(is_general)
async def stat(ctx, *args):
    await log(ctx)

#    await ctx.channel.send('Under development...')
#    return

    if len(args) != 1:
        return

    name = str(args[0]).title()
    file_name = name + '.html'

    async with ctx.channel.typing():
        retcode, stdout, stderr = await simc_(name, True)

    if retcode:
        await ctx.channel.send(ctx.author.mention + ' something went wrong with simc.')
        return

    dps = get_dps(stdout)
    class_, spec = get_class_spec(stdout)

    message = ctx.author.mention + '\n'
    message += f'**Character:** {name}, {spec} {class_}\n'
    message += f'**DPS:** {dps}\n'
    message += f'**Stat weights:**\n'
    message += get_scale(stdout, name)
    message += get_simc_ver(stdout)
    
    fp = open(file_name, 'rb')
    await ctx.channel.send(content=message, file=discord.File(fp, file_name))
    fp.close()
    
    os.remove(file_name)

@bot.command(name='clear', help='Clean messages older than a week')
@commands.check(is_me)
async def clear(ctx):
    await log(ctx)

    message_limit = 10000

    date = datetime.datetime.now() - datetime.timedelta(days=7)

    # this method is too slow when many messages in the channels have large attachments
    # await ctx.channel.purge(limit=message_limit, before=date, oldest_first=True, bulk=False)

    count = 0

    async for message in ctx.channel.history(limit=message_limit, before=date, oldest_first=True):
        count += 1
        await message.delete()

    if str(ctx.channel) == 'wowhead':
        async for message in ctx.channel.history(limit=message_limit, oldest_first=True):
            if message.author.id != wowhead_retail_news_id:
                await message.delete()
    elif str(ctx.channel) == 'raiderio':
        async for message in ctx.channel.history(limit=message_limit, oldest_first=True):
            if message.author.id != raiderio_id:
                await message.delete()
    else:
        await ctx.channel.send(f'_Deleted {str(count)} message(s)._')

bot.run(token)
