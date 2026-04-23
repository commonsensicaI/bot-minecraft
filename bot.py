import os
import subprocess

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv(".env")  # charge le fichier .env

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print("Le bot est prêt !")


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


@bot.command()
async def start(ctx):
    await ctx.send("Démarrage du serveur...")
    subprocess.Popen(["bash", "/home/emma/minecraft-server/start.sh"])
    await ctx.send("Serveur lancé !")


bot.run(os.getenv("TOKEN"))  # toujours tout à la fin
