import asyncio
import os

import discord
import paramiko
from discord.ext import commands
from dotenv import load_dotenv
from wakeonlan import send_magic_packet

load_dotenv(".env")

intents = discord.Intents.default()
intents.message_content = True

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# État global du bot
commands_locked = False  # True pendant le démarrage (WakeOnLan)
banned_users = set()  # IDs des utilisateurs bannis

ADMIN_USER_ID = 161459562988306432  # Remplace par ton propre ID si besoin


async def ensure_ssh_connection(ctx):
    """Vérifier et reconnecter si nécessaire"""
    try:
        ssh.exec_command("echo test")
        return True
    except:
        try:
            ssh.connect(
                "192.168.1.201",
                username="emma",
                key_filename="/home/emma/.ssh/id_ed25519",
            )
            return True
        except:
            return False


def is_admin(ctx):
    """Vérifie si l'utilisateur est admin du serveur ou est toi"""
    if ctx.author.id == ADMIN_USER_ID:
        return True
    if ctx.guild:
        return ctx.author.guild_permissions.administrator
    return False


async def check_access(ctx):
    """
    Vérifie que l'utilisateur n'est pas banni et que le bot n'est pas en cooldown.
    Retourne True si la commande peut s'exécuter, False sinon.
    """
    if ctx.author.id in banned_users:
        await ctx.send("you're the bad guy")
        return False
    if commands_locked:
        await ctx.send(
            "⏳ Le bot démarre, les commandes sont désactivées pendant le démarrage. Réessaie dans quelques secondes."
        )
        return False
    return True


class MyHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
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
        embed = discord.Embed(
            title=f"Commande: !{command.name}",
            description=command.help or "No description",
            color=discord.Color.green(),
        )
        await self.get_destination().send(embed=embed)


bot = commands.Bot(command_prefix="!", intents=intents, help_command=MyHelpCommand())


@bot.event
async def on_ready():
    print("The bot is ready!")


@bot.command()
async def ping(ctx):
    """Ping the bot"""
    if not await check_access(ctx):
        return
    await ctx.send("Pong!")


@bot.command()
async def start(ctx):
    """Start the Minecraft server"""
    global commands_locked

    if not await check_access(ctx):
        return

    await ctx.send("Starting the server...")

    if not await ensure_ssh_connection(ctx):
        # Serveur éteint : on envoie le WakeOnLan et on verrouille les commandes
        await ctx.send(
            "Server shut down, sending WakeOnLan... Commands disabled for 60 seconds."
        )
        send_magic_packet("58:11:22:cd:d5:c5")

        commands_locked = True
        await asyncio.sleep(60)
        commands_locked = False

        await ctx.send(
            "✅ Cooldown terminé, les commandes sont de nouveau disponibles."
        )

        if not await ensure_ssh_connection(ctx):
            await ctx.send("The server doesn't respond after 60 seconds, contact Emma")
            return

    stdin, stdout, stderr = ssh.exec_command("pgrep java")
    output = stdout.read().decode().strip()
    if output:
        await ctx.send("The Minecraft server is already up and running!")
        return

    ssh.exec_command(
        "cd /home/emma/minecraft-server && screen -dmS minecraft bash start.sh"
    )
    await ctx.send("Minecraft server launched!")


@bot.command()
async def stop(ctx):
    """Stop the Minecraft server"""
    if not await check_access(ctx):
        return
    await ctx.send("Stopping the server...")
    await ensure_ssh_connection(ctx)
    ssh.exec_command('screen -S minecraft -X stuff "stop\n"')
    await ctx.send("Minecraft server stopped!")


@bot.command()
async def status(ctx):
    """Get the Minecraft server status"""
    if not await check_access(ctx):
        return
    try:
        await ctx.send("Getting the server status...")
        if not await ensure_ssh_connection(ctx):
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


@bot.command()
async def shutdown(ctx):
    """Shutdown the Minecraft server"""
    if not await check_access(ctx):
        return
    await ctx.send("Shutting down the server...")
    await ensure_ssh_connection(ctx)
    ssh.exec_command("sudo shutdown now")
    await ctx.send("Minecraft server totally stopped!")


@bot.command()
async def badguy(ctx, user_id: int = None):
    """[Admin] Bannir un utilisateur des commandes du bot. Usage: !badguy <user_id>"""
    if not is_admin(ctx):
        await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.")
        return
    if user_id is None:
        await ctx.send("Usage: `!badguy <user_id>`")
        return
    banned_users.add(user_id)
    await ctx.send(f"<@{user_id}> you're the bad guy 😈")


@bot.command()
async def goodguy(ctx, user_id: int = None):
    """[Admin] Réactiver les commandes pour un utilisateur. Usage: !goodguy <user_id>"""
    if not is_admin(ctx):
        await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.")
        return
    if user_id is None:
        await ctx.send("Usage: `!goodguy <user_id>`")
        return
    banned_users.discard(user_id)
    await ctx.send(f"<@{user_id}> est réhabilité ✅")


bot.run(os.getenv("TOKEN"))
