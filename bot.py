import os
import discord
import asyncio
from dotenv import load_dotenv
from discord.ext import commands
from datetime import timedelta, datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN") # Gets token from .env file

intents = discord.Intents.all() # Intents give the bot various permissions in discord (Currently set to all)

bot = commands.Bot(command_prefix='!', intents=intents) # Create the bot object, commands in discord must have the '!' prefix

# Runs once when discord bot is first run
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!') # Prints to terminal that the bot is connected



async def main():
    async with bot:
        await bot.load_extension("cogs.calendar")  # Load the cog
        await bot.start(TOKEN)

asyncio.run(main())




