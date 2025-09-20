# Step 1: Send login URL
@bot.command()
async def link(ctx):
    account = get_account(ctx.author.id)
    if account.is_authenticated:
        await ctx.author.send("✅ You are already linked to Outlook.")
        return

    auth_url, state = account.con.get_authorization_url(scopes=SCOPES)
    bot.oauth_states = getattr(bot, "oauth_states", {})
    bot.oauth_states[ctx.author.id] = state

    await ctx.author.send(
        f"🔗 Please log in here:\n{auth_url}\n\n"
        "After login, copy the FULL URL you are redirected to "
        "(it starts with `http://localhost...`) and send it here with:\n"
        "`!verify <that_url>`"
    )

# Step 2: Parse full URL instead of raw code
@bot.command()
async def verify(ctx, redirect_url: str):
    account = get_account(ctx.author.id)
    state = bot.oauth_states.get(ctx.author.id, None)

    if not state:
        await ctx.author.send("⚠️ No login session found. Run `!link` first.")
        return

    try:
        parsed = urlparse(redirect_url)
        query_params = parse_qs(parsed.query)
        code = query_params.get("code", [None])[0]
        state_from_url = query_params.get("state", [None])[0]
    except Exception:
        await ctx.author.send("❌ Invalid URL. Please paste the full redirect link.")
        return

    if not code:
        await ctx.author.send("❌ Could not find `code` in that URL.")
        return

    if state_from_url != state:
        await ctx.author.send("⚠️ State mismatch. Please try `!link` again.")
        return

    result = account.con.request_token(code, state=state)
    if result:
        tokens = load_tokens()
        tokens[str(ctx.author.id)] = account.con.token_backend.token
        save_tokens(tokens)
        await ctx.author.send("✅ Successfully linked your Outlook account!")
    else:
        await ctx.author.send("❌ Failed to verify code. Please try again.")