# Bot Discord: /mclist – lista graczy + auto status (Minecraft Java)
# GOTOWE POD RAILWAY
# Python 3.10+
# requirements.txt:
# discord.py
# mcstatus

import discord
from discord import app_commands
from mcstatus import JavaServer
import asyncio
import os

# Zmienne środowiskowe (Railway → Variables)
TOKEN = os.getenv("DISCORD_TOKEN")
JAVA_SERVER_IP = os.getenv("JAVA_SERVER_IP", "play.twojserwer.pl:25565")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# 🔄 Auto status bota
async def update_status():
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            server = JavaServer.lookup(JAVA_SERVER_IP)
            status = server.status()

            online = status.players.online
            activity = discord.Game(name=f"MC Online: {online}")
            await client.change_presence(activity=activity, status=discord.Status.online)
        except:
            await client.change_presence(
                activity=discord.Game(name="MC offline"),
                status=discord.Status.idle
            )

        await asyncio.sleep(60)

@client.event
async def on_ready():
    await tree.sync()
    client.loop.create_task(update_status())
    print(f"Zalogowano jako {client.user}")

# 🎮 /mclist
@tree.command(name="mclist", description="Pokazuje graczy online na serwerze Minecraft")
async def mclist(interaction: discord.Interaction):
    try:
        server = JavaServer.lookup(JAVA_SERVER_IP)
        status = server.status()

        online = status.players.online
        max_players = status.players.max

        if status.players.sample:
            players = ", ".join(p.name for p in status.players.sample)
        else:
            players = "Brak danych / gracze ukryci"

        embed = discord.Embed(
            title="🎮 Minecraft – Status serwera",
            color=0x00ff00
        )
        embed.add_field(
            name="Gracze online",
            value=f"{online}/{max_players}",
            inline=False
        )
        embed.add_field(
            name="Lista graczy",
            value=players,
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    except Exception:
        await interaction.response.send_message(
            "❌ Serwer Minecraft jest offline",
            ephemeral=True
        )

client.run(TOKEN)
