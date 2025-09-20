import discord
import os
import json
import dateparser
import re
import shlex
from discord.ext import commands, tasks
from O365 import Account
from urllib.parse import urlparse, parse_qs
from datetime import timedelta, datetime


DATA_FILE = 'channels.json'
TOKEN_FILE = "tokens.json"
REMINDERS_FILE = 'reminders.json'

CLIENT_ID = "f8c63893-e925-46a7-85ae-3ccabf67849e"
CLIENT_SECRET = "d02cfdf7-35dd-4720-9666-cac14082b1f6"
CREDENTIALS = (CLIENT_ID, CLIENT_SECRET)
SCOPES = ['basic', 'calendar_all']
AUTH_URL = "https://almanacbot.ciamlogin.com/almanacbot.onmicrosoft.com/oauth2/v2.0/authorize?client_id=f8c63893-e925-46a7-85ae-3ccabf67849e&nonce=3EXBLHa9gC&redirect_uri=http://localhost:8000&scope=openid&response_type=code&prompt=login&code_challenge_method=S256&code_challenge=V1Y7btjN1n6T97yqovmwp8fgimg5bn5Axt3sqkYKJEA"

ERROR = "❌ Error"
SUCCESS = "✅ Success"

def load_output_channels():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_output_channels(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        return {}
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=4)

def get_account(guild_id: int):
    tokens = load_tokens()
    account = Account(CREDENTIALS)

    if str(guild_id) in tokens:
        account.con.token_backend.token = tokens[str(guild_id)]
    return account

def load_reminders():
    try:
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_reminders(data):
    with open(REMINDERS_FILE, "w") as f:
        json.dump(data, f, indent=4)


class Calendar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.output_channels = load_output_channels()
        

    async def cog_load(self):
        print("[Calendar Cog] Loaded!")
        if not self.reminder_checker.is_running():
            self.reminder_checker.start()

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

    @calendar.command(name='create_event', help='Creates a calendar event')
    async def calendar_create_event(self, ctx, *, args: str):
        output_channels = load_output_channels()
        guild_id = str(ctx.guild.id)
        channel_id = output_channels.get(guild_id)

        reminders = load_reminders()
        account = get_account(ctx.guild.id)
        schedule = account.schedule()
        calendar = schedule.get_default_calendar()

        arguments = shlex.split(args) # Split args into a list of strings
        
        # Check that there is at least a title and start time or throws an error message
        if len(arguments) < 2:
            embed = discord.Embed(
                title=ERROR,
                description="Usage: !createevent \"Title\" \"Start\" [End/Duration] [--remind 15m] [@Role]",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Set default values if additional arguments are not entered
        title = arguments[0]
        start_str = arguments[1]
        end_or_duration = None # Allows users to input either an end time or duration
        remind_before = "360m" # Default reminder time is 6 hours before
        role = None
        end_dt = None

        #Parse additional arguments
        i = 2 # If only 2 arguments then don't have to parse them
        while i < len(arguments):
            argument = arguments[i]
            if argument == "--remind" and i + 1 < len(arguments):
                remind_before = arguments[i+1]
                i += 2
            elif re.match(r"^<@&\d+>$", argument): # Checks if argument is a discord roll
                role_id = int(argument.strip("<@&>"))
                role = ctx.guild.get_role(role_id) # Gets the role id
                i += 1
            else:
                end_or_duration = argument
                i += 1

        # Date Parsing
        
        start_dt = dateparser.parse(start_str)
        if not start_dt:
            embed = discord.Embed(
                title = ERROR,
                description = "Cound not understand start date/time. Please try again.",
                color = discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if end_or_duration:
            duration_match = re.match(r"^(\d+)(m|h)$", end_or_duration.lower())
            if duration_match:
                amount, unit = duration_match.groups()
                amount = int(amount)
                end_dt = start_dt + timedelta(minutes=amount) if unit == "m" else start_dt + timedelta(hours=amount)
            else:
                end_dt = dateparser.parse(end_or_duration)

        if not end_dt:
            end_dt = start_dt + timedelta(hours=1)  # default 1-hour event

        # Create Outlook Event
        event = calendar.new_event()
        event.subject = title
        event.start = start_dt
        event.end = end_dt
        event.save()

        # Calculate Reminder Time
        remind_match = re.match(r"^(\d+)(m|h)$", remind_before.lower())
        if remind_match:
            amount, unit = remind_match.groups()
            amount = int(amount)
            delta = timedelta(minutes=amount) if unit == "m" else timedelta(hours=amount)
            reminder_time = start_dt - delta
        else:
            reminder_time = start_dt - timedelta(minutes=360)

        # Store reminder infomation
        reminders.append({
            "event_subject": title,
            "reminder_time": reminder_time.isoformat(),
            "channel_id": channel_id,
            "role_id": role.id if role else None
        })
        save_reminders(reminders)

        
        embed = discord.Embed(
            title=SUCCESS,
            description=f"**{title}**\n📅 {start_dt.strftime('%A, %B %d %Y')}\n⏰ {start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}\n🔔 Reminder: {remind_before} before start",
            color=discord.Color.green()
        )
        if role:
            embed.add_field(name="Ping Role", value=role.mention)
        await ctx.send(embed=embed)

        

    @calendar.command(name='delete', help='Deletes a calendar event')
    async def calendar_delete(self, ctx):
        embed = discord.Embed(
            title="🗑️ Event Deleted",
            description="The calendar event has been deleted.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @calendar.command(name='get_register_link', help='Registers calendar')
    async def calendar_get_register_link(self, ctx):
        account = get_account(ctx.guild.id)
        
        
        if account.is_authenticated:
            await ctx.send("Your Outlook account is linked")
            return
        auth_url, state = account.con.get_authorization_url(requested_scopes=SCOPES)
        self.bot.oauth_states = getattr(self.bot, "oauth_states", {})
        self.bot.oauth_states[ctx.guild.id] = state

        await ctx.author.send(
            f"🔗 Please log in here:\n{AUTH_URL}\n\n"
            "After login, copy the FULL URL you are redirected to "
            "(it starts with `http://localhost...`) and send it here with:\n"
            "`!calendar paste_link <that_url>`"
        )
    
    @calendar.command(name='paste_link')
    async def calendar_paste_register_link(self, ctx, redirect_url: str):
        account = get_account(ctx.guild.id)
        state = self.bot.oauth_states.get(ctx.guild.id, None)

        if not state:
            embed = discord.Embed(
                title=ERROR,
                description=f"No login session found. Run `!calendar get_register_link` first.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        try:
            parsed = urlparse(redirect_url)
            query_params = parse_qs(parsed.query)
            code = query_params.get("code", [None])[0]
            state_from_url = query_params.get("state", [None])[0]
        except Exception:
            embed = discord.Embed(
                title=ERROR,
                description = f"Invalid URL. Please paste the full redirect link.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if not code:
            embed = discord.Embed(
                title=ERROR,
                description = f"Could not find `code` in that URL.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if state_from_url != state:
            embed = discord.Embed(
                title=ERROR,
                description = f"State mismatch. Please try `!calendar get_register_link` again.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        result = account.con.request_token(code, state=state)
        if result:
            tokens = load_tokens()
            tokens[str(ctx.author.id)] = account.con.token_backend.token
            save_tokens(tokens)

            embed = discord.Embed(
                title=SUCCESS,
                description = f"Successfully linked your Outlook account!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        
        else:
            embed = discord.Embed(
                title=ERROR,
                description = f"Failed to verify code. Please try again.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        

    @calendar.command(name='set_output', help='Sets Output Channel')
    async def calendar_set_output(self, ctx, channel: discord.TextChannel):
        
        guild_id = str(ctx.guild.id)
        self.output_channels[guild_id] = channel.id
        save_output_channels(self.output_channels)
        
        embed = discord.Embed(
            title=SUCCESS,
            description=f"Output channel set to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @calendar.command(name='pingrole', help='Pings the specified role')
    async def pingrole(self, ctx, role: discord.Role):
        # Mention the role in a message
        output_channels = load_output_channels()
        guild_id = str(ctx.guild.id)
        channel_id = output_channels.get(guild_id)

        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(f"{role.mention} has been pinged!", allowed_mentions=discord.AllowedMentions(roles=True))

    @tasks.loop(minutes=10)
    async def reminder_checker(self):
    
        reminders = load_reminders()
        now = datetime.now()
        to_remove = []
        for reminder in reminders:
            reminder_time = datetime.fromisoformat(reminder["reminder_time"])
            if now >= reminder_time:
                channel = self.bot.get_channel(reminder["channel_id"])
                if channel:
                    role_mention = f"<@&{reminder['role_id']}>" if reminder["role_id"] else ""
                    await channel.send(f"🔔 **Reminder:** {reminder['event_subject']} starts soon! {role_mention}")
                to_remove.append(reminder)

        for r in to_remove:
            reminders.remove(r)
        if to_remove:
            save_reminders(reminders)      

    def cog_unload(self):
        if self.reminder_checker.is_running():
            self.reminder_checker.cancel()

    @reminder_checker.before_loop
    async def before_reminder_checker(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Calendar(bot))