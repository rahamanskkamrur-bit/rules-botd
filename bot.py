
import asyncio
import os
from aiohttp import web
import discord
from discord.ext import commands

# =====================================================================
# 1. BOT & RULES CONFIGURATION
# =====================================================================

# Render will read this from your Environment Variables (Key: BOT_TOKEN)
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Default Banner Image shown at the bottom of the Rules Embed
# You can replace this link with any image URL you like!
RULES_BANNER_URL = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80"

# Optional: Put a Role ID here if you want the "Agree to Rules" button to give a role (leave as 0 to disable)
VERIFIED_ROLE_ID = 0

BOT_STATUS = "Starting up..."


# =====================================================================
# 2. KEEP-ALIVE WEB SERVER (Required for Render Web Services)
# =====================================================================

async def handle_ping(request):
    return web.Response(text=f"Render Rules Bot is running!\nDiscord Bot Status: {BOT_STATUS}")

async def run_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Keep-alive web server bound to port {port}")


# =====================================================================
# 3. RULES EMBED & INTERACTIVE BUTTON
# =====================================================================

def create_rules_embed(guild: discord.Guild = None, custom_image_url: str = None) -> discord.Embed:
    server_name = guild.name if guild else "Our Server"

    embed = discord.Embed(
        title=f"📜 {server_name} — Official Server Rules",
        description=(
            "Welcome to the community! To keep this server a safe, fun, and welcoming place "
            "for everyone, please read and follow the rules below at all times.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="1️⃣ Be Respectful to Everyone",
        value=(
            "Treat all members with respect and kindness. Harassment, toxic behavior, hate speech, "
            "racism, sexism, or personal attacks will result in immediate action."
        ),
        inline=False,
    )

    embed.add_field(
        name="2️⃣ No Spamming or Self-Promotion",
        value=(
            "Do not flood chat with repeated messages, excessive emojis, soundboards, or mass pings. "
            "Advertising other Discord servers, links, or services in chat or DMs is strictly prohibited."
        ),
        inline=False,
    )

    embed.add_field(
        name="3️⃣ Keep Content Safe (No NSFW)",
        value=(
            "This is a community server. Sharing NSFW, explicit, gore, disturbing, or illegal media/links "
            "anywhere in the server will result in an instant ban."
        ),
        inline=False,
    )

    embed.add_field(
        name="4️⃣ Use the Correct Channels",
        value=(
            "Keep conversations and commands in their designated channels. Check channel names and "
            "descriptions before posting."
        ),
        inline=False,
    )

    embed.add_field(
        name="5️⃣ Protect Personal Privacy",
        value=(
            "Do not share private information (doxxing), real-life photos, or confidential details of "
            "yourself or any other member."
        ),
        inline=False,
    )

    embed.add_field(
        name="6️⃣ Respect Staff & Open Tickets for Help",
        value=(
            "Follow instructions from staff members. Do not argue about moderation in public chat—if you "
            "need support, want to report someone, or wish to appeal a punishment, please open a ticket."
        ),
        inline=False,
    )

    embed.add_field(
        name="7️⃣ Follow Discord Terms of Service",
        value=(
            "All members must comply with [Discord's Terms of Service](https://discord.com/terms) and "
            "[Community Guidelines](https://discord.com/guidelines)."
        ),
        inline=False,
    )

    # Set server icon as thumbnail if available
    if guild and guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    # Set the banner image at the bottom of the embed
    image_to_use = custom_image_url or RULES_BANNER_URL
    if image_to_use:
        embed.set_image(url=image_to_use)

    embed.set_footer(text=f"{server_name} Staff Team • Breaking rules may result in a warning, mute, kick, or ban.")
    return embed


class RulesAgreeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="I Have Read & Agree to the Rules",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="rules_panel:agree",
    )
    async def agree_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if VERIFIED_ROLE_ID and interaction.guild:
            role = interaction.guild.get_role(VERIFIED_ROLE_ID)
            if role:
                if role in interaction.user.roles:
                    await interaction.response.send_message(
                        "✅ You have already agreed to the rules and are verified!",
                        ephemeral=True,
                    )
                    return
                try:
                    await interaction.user.add_roles(role, reason="Agreed to server rules")
                    await interaction.response.send_message(
                        f"✅ Thank you for agreeing to the rules! You have been given the {role.mention} role.",
                        ephemeral=True,
                    )
                    return
                except discord.Forbidden:
                    pass

        await interaction.response.send_message(
            "✅ Thank you for reading and agreeing to the server rules! Enjoy your stay.",
            ephemeral=True,
        )


# =====================================================================
# 4. BOT SETUP & COMMANDS
# =====================================================================

class RulesBot(commands.Bot):
    def __init__(self, use_message_content: bool = True):
        intents = discord.Intents.default()
        intents.message_content = use_message_content
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(RulesAgreeView())
        await self.tree.sync()

    async def on_ready(self):
        global BOT_STATUS
        BOT_STATUS = f"ONLINE as {self.user} (ID: {self.user.id})"
        print(f"✅ SUCCESS! Rules Bot is ONLINE as: {self.user}")


def register_commands(bot_instance: RulesBot):
    @bot_instance.command(name="rules")
    @commands.has_permissions(administrator=True)
    async def send_rules_prefix(ctx: commands.Context, image_url: str = None):
        embed = create_rules_embed(ctx.guild, image_url)
        await ctx.send(embed=embed, view=RulesAgreeView())
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    @bot_instance.tree.command(name="rules", description="Post the official server rules embed with an image banner")
    @discord.app_commands.describe(image_url="Optional: Custom image URL for the bottom of the rules embed")
    async def slash_rules(interaction: discord.Interaction, image_url: str = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can post the rules panel.", ephemeral=True)
            return

        embed = create_rules_embed(interaction.guild, image_url)
        await interaction.channel.send(embed=embed, view=RulesAgreeView())
        await interaction.response.send_message("✅ Server rules embed posted!", ephemeral=True)


async def main():
    global BOT_STATUS
    await run_web_server()

    if not BOT_TOKEN:
        BOT_STATUS = "ERROR: BOT_TOKEN environment variable is missing in Render!"
        print(f"❌ {BOT_STATUS}")
        while True:
            await asyncio.sleep(3600)

    bot = RulesBot(use_message_content=True)
    register_commands(bot)

    try:
        print("🔄 Connecting to Discord...")
        await bot.start(BOT_TOKEN)
    except discord.PrivilegedIntentsRequired:
        print("⚠️ Message Content Intent not enabled. Falling back to default intents (Slash command /rules will work!)...")
        await bot.close()
        bot = RulesBot(use_message_content=False)
        register_commands(bot)
        await bot.start(BOT_TOKEN)
    except discord.LoginFailure:
        BOT_STATUS = "ERROR: Invalid Bot Token! Reset your token in Discord Developer Portal and update Render."
        print(f"❌ {BOT_STATUS}")
        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        BOT_STATUS = f"ERROR: {type(e).__name__}: {e}"
        print(f"❌ {BOT_STATUS}")
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
  
