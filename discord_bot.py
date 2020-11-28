# discord_bot.py
import os
import subprocess
import random
import dotenv
import sys
import discord
from discord.ext import commands

dotenv.load_dotenv()

TOKEN = os.getenv('TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
MYSELF_ID = int(os.getenv('MYSELF_ID'))
MISC_CHANNEL_ID = int(os.getenv('MISC_CHANNEL_ID'))

bot = commands.Bot(command_prefix='!')

async def is_me(ctx):
	return ctx.author.id == MYSELF_ID

async def is_misc_channel(ctx):
	return ctx.channel.id == MISC_CHANNEL_ID

@bot.command(name='debug', help='For debugging use only')
@commands.check(is_me)
async def debug(ctx):
	print(os.getenv('SIMC'))

@bot.command(name='roll', help='Simulates rolling dice')
@commands.check(is_misc_channel) # only text channel "misc" can trigger the command
async def roll(ctx, *args):
	if len(args) == 0:
		sides = 100
	elif args[0].isdigit():
		sides = int(args[0])
		if sides <= 0 or sides > sys.maxsize:
			return
	else:
		return

	message = str(ctx.author.name)
	message += ' rolled **' + str(random.choice(range(1, sides + 1))) + '** out of **' + str(sides) + '**.'

	await ctx.send(message)

@bot.command(name='simc', help='Run a quick sim in SimulationCraft on a character in Illidan - US')
@commands.check(is_misc_channel)
async def simc(ctx, *args):
	if len(args) != 1:
		return

	if ctx.author.id != MYSELF_ID:
		await ctx.send('You are not allowed to use this feature yet.')
		return

	name = str(args[0]).title()

	file_name = name + '.html'

	cmd = os.getenv('SIMC')
	cmd += ' armory=us,illidan,' + name.lower()
	cmd += ' calculate_scale_factors=0 threads=1 process_priority=low html=' + file_name

	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

	stdout, stderr = p.communicate()
	retcode = p.wait()

	if retcode:
		await ctx.send(ctx.author.mention + ' Character ' + name + ' - Illidan not found')
		return

	output = stdout.decode("utf-8")

	i1 = output.find('DPS=', 0, len(output)) + 4
	i2 = output.find('.', i1, len(output)) + 3

	dps = output[i1:i2]

	i1 = output.find('Player:', 0, len(output)) + len('Player: ') + len(name) + 1
	i1 = output.find(' ', i1, len(output)) + 1
	i2 = output.find(' ', i1, len(output))

	class_ = output[i1:i2]
	if class_ == 'demenhunter':
		class_ = 'demen hunter'
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
	message += '**Character:** ' + name + ' - Illidan, ' + spec + ' ' + class_ + '\n'
	message += '**DPS:** ' + dps + '\n'
	message += '(simc verion ' + simc_ver + ', wow version ' + wow_ver + ')\n'

	await ctx.send(message)

	fp = open(file_name, 'rb')
	await ctx.channel.send(file=discord.File(fp, file_name))
	fp.close()

	os.remove(file_name)

bot.run(TOKEN)