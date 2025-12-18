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
import json
from datetime import datetime

# Zmienne środowiskowe (Railway → Variables)
TOKEN = os.getenv("DISCORD_TOKEN")
JAVA_SERVER_IP = os.getenv("JAVA_SERVER_IP", "play.twojserwer.pl:25565")

STATS_FILE = "stats.json"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# 📊 zapis statystyk
async def save_stats():
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            server = JavaServer.lookup(JAVA_SERVER_IP)
            status = server.status()
            online = status.players.online

            data = []
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, "r") as f:
                    data = json.load(f)

            data.append({
                "time": datetime.utcnow().isoformat(),
                "online": online
            })

            # zachowaj max 7 dni (10080 minut)
            data = data[-10080:]

            with open(STATS_FILE, "w") as f:
                json.dump(data, f)
        except:
            pass

        await asyncio.sleep(60)

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
    client.loop.create_task(save_stats())
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
        embed.add_field(name="Gracze online", value=f"{online}/{max_players}", inline=False)
        embed.add_field(name="Lista graczy", value=players, inline=False)

        await interaction.response.send_message(embed=embed)
    except Exception:
        await interaction.response.send_message("❌ Serwer Minecraft jest offline", ephemeral=True)

# 📊 /mcstats
@tree.command(name="mcstats", description="Statystyki online (24h)")
async def mcstats(interaction: discord.Interaction):
    if not os.path.exists(STATS_FILE):
        await interaction.response.send_message("❌ Brak danych statystycznych", ephemeral=True)
        return

    with open(STATS_FILE, "r") as f:
        data = json.load(f)

    last_24h = data[-1440:]
    online_values = [d["online"] for d in last_24h]

    if not online_values:
        await interaction.response.send_message("❌ Brak danych", ephemeral=True)
        return

    avg_online = sum(online_values) // len(online_values)
    max_online = max(online_values)

    embed = discord.Embed(
        title="📊 Statystyki Minecraft (24h)",
        color=0x3498db
    )
    embed.add_field(name="Średnio online", value=str(avg_online), inline=True)
    embed.add_field(name="Max online", value=str(max_online), inline=True)
    embed.add_field(name="Próbki", value=f"{len(online_values)} min", inline=False)

    await interaction.response.send_message(embed=embed)

# 🏆 /mctop – top godziny grania
@tree.command(name="mctop", description="Top godziny grania (ostatnie 7 dni)")
async def mctop(interaction: discord.Interaction):
    if not os.path.exists(STATS_FILE):
        await interaction.response.send_message("❌ Brak danych", ephemeral=True)
        return

    with open(STATS_FILE, "r") as f:
        data = json.load(f)

    hours = {}
    for entry in data:
        hour = datetime.fromisoformat(entry["time"]).hour
        hours.setdefault(hour, []).append(entry["online"])

    avg_per_hour = {
        h: sum(v) // len(v)
        for h, v in hours.items()
    }

    top_hours = sorted(avg_per_hour.items(), key=lambda x: x[1], reverse=True)[:5]

    desc = "
".join([
        f"🕒 **{h:02d}:00** → {v} graczy"
        for h, v in top_hours
    ])

    embed = discord.Embed(
        title="🏆 Top godziny grania",
        description=desc or "Brak danych",
        color=0xf1c40f
    )

    await interaction.response.send_message(embed=embed)

client.run(TOKEN)
