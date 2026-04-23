import asyncio
import os
import re
import subprocess
import time
from tokenize import Name

import discord
import paramiko
import psutil
from discord.ext import commands
from dotenv import load_dotenv
from wakeonlan import send_magic_packet

load_dotenv(".env")  # load the .env file

intents = discord.Intents.default()
intents.message_content = True

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


async def ensure_ssh_connection(ctx):
    """Vérifier et reconnecter si nécessaire"""
    try:
        ssh.exec_command("echo test")
        return True
    except:
        # Not connected, we try again once
        try:
            ssh.connect(
                "192.168.1.201",
                username="emma",
                key_filename="/home/emma/.ssh/id_ed25519",
            )
            return True
        except:
            return False


class MyHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        """Send all available commands"""
        embed = discord.Embed(title="Commands available", color=discord.Color.blue())

        for cog, commands_list in mapping.items():
            command_names = [cmd.name for cmd in commands_list if not cmd.hidden]
            if command_names:
                embed.add_field(
                    name=cog.qualified_name if cog else "General",
                    value=", ".join(command_names),
                    inline=False,
                )

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        """Send help for a specific command"""
        embed = discord.Embed(
            title=f"Commande: !{command.name}",
            description=command.help or "No description",
            color=discord.Color.green(),
        )
        await self.get_destination().send(embed=embed)


bot = commands.Bot(command_prefix="!", intents=intents, help_command=MyHelpCommand())


@bot.command()
async def ping(ctx):
    """Ping the bot"""
    await ctx.send("Pong!")


@bot.event
async def on_ready():
    print("Le bot est prêt !")


@bot.command()
async def start(ctx):
    """Start the Minecraft server"""
    await ctx.send("Starting the server...")

    # Try SSH connection
    if not await ensure_ssh_connection(ctx):
        # Server is shut down, we send WakeOnLan
        await ctx.send("Server shut down, sending WakeOnLan...")
        send_magic_packet("58:11:22:cd:d5:c5")
        await asyncio.sleep(60)

        if not await ensure_ssh_connection(ctx):
            await ctx.send("The server doesn't respond after 60 seconds, contact Emma")
            return

    # Here we are connected in all cases
    stdin, stdout, stderr = ssh.exec_command("pgrep java")
    output = stdout.read().decode().strip()
    if output:
        await ctx.send("The Minecraft server is already up and running!")
        return

    # Java does not run, we start it
    ssh.exec_command(
        "cd /home/emma/minecraft-server && screen -dmS minecraft bash start.sh"
    )
    await ctx.send("Minecraft server launched!")


@bot.command()
async def stop(ctx):
    """Stop the Minecraft server"""
    await ctx.send("Stopping the server...")
    ssh.exec_command('screen -S minecraft -X stuff "stop\n"')
    await ctx.send("Minecraft server stopped!")


@bot.command()
async def status(ctx):
    """Get the Minecraft server status"""
    try:
        await ctx.send("Getting the server status...")
        if not await ensure_ssh_connection(ctx):
            # Server is shut down, we send WakeOnLan
            await ctx.send("Server shut down")
            return
        stdin, stdout, stderr = ssh.exec_command("pgrep java")
        output = stdout.read().decode().strip()
        if output:
            await ctx.send("The Minecraft server is up and running!")
        else:
            await ctx.send("The Minecraft server is not running.")
    except:
        await ctx.send("An error occurred while getting the server status.")


bot.run(os.getenv("TOKEN"))  # always at the end
