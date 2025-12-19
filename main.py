import discord
from discord import app_commands
from mcstatus import JavaServer
import asyncio
import os
import json
from datetime import datetime
from keep_alive import keep_alive

TOKEN = os.getenv("DISCORD_TOKEN")
JAVA_SERVER_IP = os.getenv("JAVA_SERVER_IP")

STATS_FILE = "stats.json"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

async def update_status():
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            status = JavaServer.lookup(JAVA_SERVER_IP).status()
            online = status.players.online
            await client.change_presence(
                activity=discord.Game(name=f"MC Online: {online}")
            )
        except:
            await client.change_presence(
                activity=discord.Game(name="MC offline"),
                status=discord.Status.idle
            )
        await asyncio.sleep(60)

async def save_stats():
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            online = JavaServer.lookup(JAVA_SERVER_IP).status().players.online
            data = []
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE) as f:
                    data = json.load(f)
            data.append({
                "time": datetime.utcnow().isoformat(),
                "online": online
            })
            data = data[-10080:]
            with open(STATS_FILE, "w") as f:
                json.dump(data, f)
        except:
            pass
        await asyncio.sleep(60)

@client.event
async def on_ready():
    await tree.sync()
    client.loop.create_task(update_status())
    client.loop.create_task(save_stats())
    print(f"Zalogowano jako {client.user}")

@tree.command(name="mclist", description="Lista graczy online")
async def mclist(interaction: discord.Interaction):
    try:
        status = JavaServer.lookup(JAVA_SERVER_IP).status()
        players = ", ".join(p.name for p in status.players.sample) if status.players.sample else "Brak danych"
        embed = discord.Embed(title="🎮 Minecraft Status", color=0x00ff00)
        embed.add_field(name="Online", value=f"{status.players.online}/{status.players.max}", inline=False)
        embed.add_field(name="Gracze", value=players, inline=False)
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("❌ Serwer offline", ephemeral=True)

@tree.command(name="mcstats", description="Statystyki 24h")
async def mcstats(interaction: discord.Interaction):
    if not os.path.exists(STATS_FILE):
        await interaction.response.send_message("Brak danych", ephemeral=True)
        return
    with open(STATS_FILE) as f:
        data = json.load(f)[-1440:]
    values = [d["online"] for d in data]
    embed = discord.Embed(title="📊 Statystyki 24h", color=0x3498db)
    embed.add_field(name="Średnia", value=str(sum(values)//len(values)))
    embed.add_field(name="Max", value=str(max(values)))
    await interaction.response.send_message(embed=embed)

@tree.command(name="mctop", description="Top godziny grania")
async def mctop(interaction: discord.Interaction):
    with open(STATS_FILE) as f:
        data = json.load(f)
    hours = {}
    for d in data:
        h = datetime.fromisoformat(d["time"]).hour
        hours.setdefault(h, []).append(d["online"])
    top = sorted(((h, sum(v)//len(v)) for h,v in hours.items()), key=lambda x: x[1], reverse=True)[:5]
    desc = "\n".join(f"🕒 {h:02d}:00 → {v}" for h,v in top)
    embed = discord.Embed(title="🏆 Top godziny grania", description=desc, color=0xf1c40f)
    await interaction.response.send_message(embed=embed)

keep_alive()
client.run(TOKEN)
