import discord
import aiohttp
from discord import app_commands
from discord.ext import tasks

BASE_URL = ""
GET_SERVER_STATE_ENDPOINT = "/get_server_state"
GUILD_ID = 1377942591169105942

# --- Slash command ---
async def info(interaction: discord.Interaction):
    url = BASE_URL + GET_SERVER_STATE_ENDPOINT
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    server_name = data.get("server_name", "Unknown")
                    online_players = data.get("online_players", "Unknown")
                    uptime_seconds = data.get("uptime_seconds", "Unknown")
                    reply = (
                        "```\n"
                        f"{'Server:':15} {server_name}\n"
                        f"{'Online Players:':15} {online_players}/128 players\n"
                        f"{'Uptime:':15} {uptime_seconds/60:.2f}/120 minutes\n"
                        "```"
                    )
                else:
                    reply = "Failed to fetch server info."
        except Exception:
            reply = "Error fetching server info."
    await interaction.response.send_message(reply)


# --- Bot class ---
class ToWUtils(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        # Clear all existing commands in the guild to remove ghosts
        self.tree.clear_commands(guild=guild)
        # Add the single /info command
        self.tree.add_command(app_commands.Command(name="info", description="Get server info and player count", callback=info), guild=guild)
        await self.tree.sync(guild=guild)
        self.update_status_task.start()

    @tasks.loop(seconds=60)
    async def update_status_task(self):
        url = BASE_URL + GET_SERVER_STATE_ENDPOINT
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        online_players = data.get("online_players", "0")
                        await self.change_presence(
                            activity=discord.Game(name=f"{online_players}/128 players online")
                        )
                    else:
                        await self.change_presence(
                            activity=discord.Game(name="Server offline")
                        )
            except Exception:
                await self.change_presence(
                    activity=discord.Game(name="Error fetching data")
                )

    @update_status_task.before_loop
    async def before_update_status(self):
        await self.wait_until_ready()


# --- Run bot ---
with open("token", "r") as file:
    token = file.read().strip()
with open("endpoint", "r") as file:
    BASE_URL = file.read().strip()

intents = discord.Intents.default()
intents.message_content = True
client = ToWUtils(intents=intents)
client.run(token)
