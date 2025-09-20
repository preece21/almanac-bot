import os
import discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN") # Gets token from .env file

intents = discord.Intents.all() # Intents give the bot various permissions in discord (Currently set to all)

bot = commands.Bot(command_prefix='!', intents=intents) # Create the bot object, commands in discord must have the '!' prefix

# Runs once when discord bot is first run
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!') # Prints to terminal that the bot is connected

# Load cogs on startup
@bot.event
async def setup_hook():
    await bot.load_extension('cogs.calendar')

bot.run(TOKEN)


