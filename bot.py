import asyncio
import os
import subprocess
import time

import discord
import paramiko
import psutil
from discord.ext import commands
from dotenv import load_dotenv
from wakeonlan import send_magic_packet

load_dotenv(".env")  # charge le fichier .env

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


@bot.event
async def on_ready():
    print("Le bot est prêt !")


@bot.command()
async def start(ctx):
    await ctx.send("Starting the server...")

    # Essai connexion SSH
    try:
        ssh.connect(
            "192.168.1.201", username="emma", key_filename="/home/emma/.ssh/id_ed25519"
        )
    except:
        # Serveur éteint, on réveille
        await ctx.send("Server shut down, sending WakeOnLan...")
        send_magic_packet("58:11:22:cd:d5:c5")
        await asyncio.sleep(60)
        try:
            ssh.connect(
                "192.168.1.201",
                username="emma",
                key_filename="/home/emma/.ssh/id_ed25519",
            )
        except:
            await ctx.send("The server doesn't respond after 60 seconds, contact Emma")
            return

    # Ici on est connecté dans tous les cas
    stdin, stdout, stderr = ssh.exec_command("pgrep java")
    output = stdout.read().decode().strip()
    if output:
        await ctx.send("The Minecraft server is already up and running!")
        return

    # Java tourne pas, on lance
    ssh.exec_command(
        "cd /home/emma/minecraft-server && nohup bash start.sh > logs/bot.log 2>&1 &"
    )
    await ctx.send("Minecraft server launched!")


bot.run(os.getenv("TOKEN"))  # toujours tout à la fin
