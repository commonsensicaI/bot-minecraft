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
async def ping(ctx):
    await ctx.send("Pong!")


@bot.command()
async def start(ctx):
    await ctx.send("Démarrage du serveur...")
    connecte = False
    try:
        ssh.connect(
            "192.168.1.201", username="emma", key_filename="/home/emma/.ssh/id_ed25519"
        )
        connecte = True
    except Exception as e:
        print(f"Erreur SSH : {e}")
        await ctx.send(f"Erreur SSH : {e}")
        await ctx.send("Serveur éteint il va s'allumer")

    if connecte:
        stdin, stdout, stderr = ssh.exec_command("pgrep java")
        output = stdout.read().decode().strip()
        if output:  # si y'a un PID c'est que java tourne
            await ctx.send("Le serveur est déjà lancé !")
            return

    send_magic_packet("58:11:22:cd:d5:c5")
    await asyncio.sleep(60)
    try:
        ssh.connect(
            "192.168.1.201", username="emma", key_filename="/home/emma/.ssh/id_ed25519"
        )
    except:
        await ctx.send("Contact Emma, she screwed up")
        return

    ssh.exec_command(
        "nohup bash /home/emma/minecraft-server/start.sh > /home/emma/minecraft-server/logs/bot.log 2>&1 &"
    )
    await ctx.send("Serveur lancé !")


bot.run(os.getenv("TOKEN"))  # toujours tout à la fin
