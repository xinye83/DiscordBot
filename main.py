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

TOKEN = os.getenv('token')
SIMC = '/home/xye/simc/engine/simc'

bot = commands.Bot(command_prefix='!')

def is_bot_owner(ctx):
    return bot.is_owner(ctx.author)

def is_not_pm(ctx):
    return ctx.guild is not None

@bot.event
async def on_ready():
    msg = f'****** Logged in successfully as {bot.user.name} (id={bot.user.id})'
    print(msg)

@bot.command(name='test', help='For development and testing')
@commands.check(is_bot_owner)
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

@bot.command(name='roll', help='Simulate a dice roll')
@commands.check(is_not_pm)
async def roll(ctx, sides: int):
    msg = ctx.author.mention

    if sides <= 0 or sides > sys.maxsize:
        msg += ' invalid roll.'
    else:
        dice = random.choice(range(1, sides + 1))
        msg += ' rolled **' + str(dice) + '** out of **' + str(sides) + '**.'

    await ctx.send(msg)

# TODO
async def simc_bl_api(name, stat=False):
    file_name = name.title() + '.html'

    if os.path.exists(file_name):
        os.remove(file_name)

    cmd = SIMC + ' armory=us,illidan,' + name.lower()
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

# TODO
def get_dps(string):
    i1 = string.find('DPS=', 0, len(string)) + 4
    i2 = string.find('.', i1, len(string)) + 3
    dps = string[i1:i2]
    return dps

# TODO
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

# TODO
def get_simc_ver(string):
    return '_' + string.partition('\n')[0] + '_'

# TODO
@bot.command(name='dps', help='Simulate DPS for character in US-Illidan (less than 5 seconds)')
async def dps(ctx, *args):
    if len(args) != 1:
        return

    name = str(args[0]).title()
    file_name = name + '.html'

    async with ctx.channel.typing():
        retcode, stdout, stderr = await simc_bl_api(name)

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

# TODO
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

# TODO
@bot.command(name='stat', help='Simulate stat weights for a character in US-Illidan (about 3 minutes)')
async def stat(ctx, *args):
    if len(args) != 1:
        return

    name = str(args[0]).title()
    file_name = name + '.html'

    async with ctx.channel.typing():
        retcode, stdout, stderr = await simc_bl_api(name, True)

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

# TODO
@bot.command(name='simc', help='This command only works in DM and accepts profiles from simc addon, remove all double quotation marks in the ouput string from the addon and pass it as a single argument to the command')
async def simc(ctx, *args):
    if ctx.guild is not None:
        return

    if len(args) != 1:
        return

    profile = str(ctx.message.id) + '.in'
    fp = open(profile, 'w')
    fp.write(args[0])
    fp.close()

    file_name = str(ctx.message.id) + '.html'

    if os.path.exists(file_name):
        os.remove(file_name)

    cmd = simc_bin + ' ' + profile 
    cmd += ' calculate_scale_factors=0'
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

    dps = get_dps(stdout)

    await ctx.channel.send(f'DPS: {dps}')

    os.remove(profile)

@bot.command(name='clean', help='Clean messages older than a week in a text channel')
@commands.check(is_not_pm)
@commands.check(is_bot_owner)
async def clean(ctx):
    async with ctx.channel.typing():
        message_limit = 10000
        date = datetime.datetime.now() - datetime.timedelta(days=7)
        count = 0

        async for message in ctx.channel.history(limit=message_limit, before=date, oldest_first=True):
            count += 1
            await message.delete()

    await ctx.channel.send(f'_Deleted {str(count)} message(s)._')

bot.run(TOKEN)
