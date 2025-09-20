import discord
import os
import json
from discord.ext import commands

DATA_FILE = 'channels.json'

def load_output_channels():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_output_channels(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

class Calendar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.output_channels = load_output_channels()

    @commands.group(name='calendar', help='Calendar command group')
    async def calendar(self, ctx):
        if ctx.invoked_subcommand is None:
            # If no subcommand is used, reply with help or usage hint
            embed = discord.Embed(
                title="📅 Calendar Commands",
                description="Available subcommands: `create`, `delete`, `register`",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @calendar.command(name='create', help='Creates a calendar event')
    async def calendar_create(self, ctx):
        embed = discord.Embed(
            title="📅 Event Created",
            description="A new calendar event has been successfully created.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @calendar.command(name='delete', help='Deletes a calendar event')
    async def calendar_delete(self, ctx):
        embed = discord.Embed(
            title="🗑️ Event Deleted",
            description="The calendar event has been deleted.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @calendar.command(name='register', help='Registers calendar')
    async def calendar_register(self, ctx):
        embed = discord.Embed(
            title="✅ Calendar Registered",
            description="You have successfully registered your calendar.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @calendar.command(name='set_output', help='Sets Output Channel')
    async def calendar_register(self, ctx, channel: discord.TextChannel):
        
        guild_id = str(ctx.guild.id)
        self.output_channels[guild_id] = channel.id
        save_output_channels(self.output_channels)
        
        embed = discord.Embed(
            title="✅ Calendar Registered",
            description=f"✅ Output channel set to {channel.mention}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @calendar.command(name='pingrole', help='Pings the specified role')
    async def pingrole(self, ctx, role: discord.Role):
        # Mention the role in a message
        await ctx.send(f"{role.mention} has been pinged!", allowed_mentions=discord.AllowedMentions(roles=True))

# Required setup for the cog
async def setup(bot):
    await bot.add_cog(Calendar(bot))
