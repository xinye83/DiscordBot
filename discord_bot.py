# bot.py
import os
import random
import dotenv
import sys
from discord.ext import commands

dotenv.load_dotenv()

TOKEN = os.getenv('TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
MYSEFL_ID = int(os.getenv('MYSEFL_ID'))
MISC_CHANNEL_ID = int(os.getenv('MISC_CHANNEL_ID'))

bot = commands.Bot(command_prefix='!')

def to_italian(string):
	return '_' + string + '_'

def to_bold(string):
	return '**' + string + '**'

async def is_me(ctx):
	print(ctx.message.author.id)
	return ctx.message.author.id == MYSEFL_ID

async def is_misc_channel(ctx):
	return ctx.message.channel.id == MISC_CHANNEL_ID

@bot.command(name='debug', help='For debugging use.')
@commands.check(is_me)
async def debug(ctx):
	print(ctx.message.author)

@bot.command(name='roll', help='Simulates rolling dice.')
@commands.check(is_misc_channel) # only text channel "misc" can trigger the command
async def roll(ctx, *args):
	if len(args) == 0:
		sides = 100
	elif args[0].isdigit():
		sides = int(args[0])
		if sides <= 0 or sides >= sys.maxsize:
			return
	else:
		return

	message = ctx.message.author.mention
	message += ' I rolled ' + to_bold(str(random.choice(range(1, sides + 1)))) + ' out of ' + to_bold(str(sides)) + '.'

	await ctx.send(message)

bot.run(TOKEN)