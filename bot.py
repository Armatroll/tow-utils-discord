import discord
import aiohttp
from discord.ext import tasks, commands
from discord import app_commands

BASE_URL = ""
GET_SERVER_STATE_ENDPOINT = "/get_server_state"
# GUILD_ID = 1377942591169105942 # TOW
GUILD_ID = 619962205713989652 # TEST



# --- Bot class ---
class ToWUtils(commands.Bot):
    async def on_ready(self):
        print(f"Logged on as {self.user}")
        try:
            myguild = discord.Object(id=GUILD_ID)
            synced = await self.tree.sync(guild=myguild)
            print(f'Synced {len(synced)} command to guild id {myguild.id}')
        except Exception as e:
            print(f'Error syncing commands : {e}')
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
with open("guild", "r") as file:
    GUILD_ID = int(file.read().strip())

intents = discord.Intents.default()
intents.message_content = True
client = ToWUtils(command_prefix="!",intents=intents)
myguild = discord.Object(id=GUILD_ID)


@client.tree.command(name="status", description="Get the server status and it's player count", guild=myguild)
async def status(interaction: discord.Interaction):
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
                        f"{'Uptime:':15} {uptime_seconds/60:.0f}/120 minutes\n"
                        "```"
                    )
                else:
                    reply = "Failed to fetch server info."
        except Exception:
            reply = "Error fetching server info."
    await interaction.response.send_message(reply, ephemeral=True)

client.run(token)
