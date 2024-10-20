import discord
import asyncio
import json

from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
  print(f"Logged in as {client.user")
  try:
    synced = await client.tree.sync()
    print(f"synced {len(synced)} command(s)")
  except Exception as e:
    print(e)

@client.tree.command(description="Get the ping of the bot")
async def ping(interaction: discord.Interaction):
  try:
    await interaction.response.send_message(f"Pong! My ping is {round(client.latency * 1000)}ms", ephemeral = True)
  except Exception as e:
    await interaction.response.send_message(f"Error: {e}", ephemeral = True)

@client.tree.command(description="Kick a member from the server")
@app_commands.describe(member="Who am i kicking from the server?")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str ="No reason provided"):
  if interaction.guild == None:
    await interaction.response.send_message("This command can only be used in a server", ephemeral = True)
  else:
    try:
      await interaction.guild.kick(member=member, reason=reason)
      await member.send(f"You were kicked in {interaction.guild.name} for {reason}")
      await interaction.response.send_message(f"Successfully kicked {member.mention} for {reason}", ephemeral = True)
    except Exception as e:
      await interaction.response.send_message(f"Error: {e}", ephemeral = True)

@client.tree.command(description="Ban a member from the server")
@app_commands.describe(member="Who am i banning from the server?", reason = "Why am i banning this member?")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
  if interaction.guild == None:
    await interaction.response.send_message("This command only works in a server", ephemeral = True)
  else:
    try:
      await interaction.guild.ban(member=member, reason=reason)
      await member.send(f"You were banned in {interaction.guild.name} for {reason}")
      await interaction.response.send_message(f"Successfully banned {member.mention} for reason {reason}", ephemeral = True)
    except Exception as e:
      await interaction.response.send_message(f"Error: {e}", ephemeral = True)

@client.tree.command(description = "Delete a certain number of messages from a channel")
@app_commands.describe(amount = "How many messages am i purging")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
  if interaction.guild == None:
    await interaction.response.send_message("This command only works in a server")
  else:
    try:
      await interaction.channel.purge(limit=amount)
      client_message = await interaction.channel.send(f"Succesfully purged {amount} message(s)")
      await asyncio.sleep(3)
      await client_message.delete()
    except Exception as e:
      await interaction.response.send_message(f"Error: {e}", ephemeral = True)

@client.tree.command(description="Unban a member from the server")
@app_commands.describe(member="Who am i unbanning from the server", reason="Why am i unbanning this user")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
  if interaction.guild == None:
    await interaction.response.send_message("This command only works in a server", ephemeral = True)
  else:
    try:
      await interaction.guild.unban(member=member, reason=reason)
      await interaction.response.send_message(f"{member.mention} has been successfully unbanned with the reason {reason}", ephemeral = True)
    except Exception as e:
      await interaction.response.send_message(f"Error: {e}", ephemeral = True")

@client.tree.command(description="Mute a member in the server")
@app_commands.describe(member="Who am i muting in the server?", time="How long am i muting the member for?", reason="Why am i muting this member?")
@app_commands.checks.has_permissions(timeout_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, time: int, reason: str = "No reason Provided"):
  if interaction.guild == None:
    await interaction.response.send_message("This command only works in a server", ephemeral = True)
  else:
    try:
      await interacion.guild.timeout(member=member, reason=reason)
      await interaction.response.send_message(f"{member.mention} has been timed out with reason {reason}", ephemeral = True)
      await member.send(f"You have been muted in {interaction.guild.name} for {reason}")
    except Exception as e:
      await interaction.response.send_message(f"Error: {e}", ephemeral = True)

WARNINGS_FILE = "warnings.json"

# Load warnings from JSON file or create a new one
def load_warnings():
    if os.path.exists(WARNINGS_FILE):
        with open(WARNINGS_FILE, "r") as f:
            return json.load(f)
    return {}

# Save warnings to the JSON file
def save_warnings(warnings):
    with open(WARNINGS_FILE, "w") as f:
        json.dump(warnings, f, indent=4)

# Initialize warnings dictionary from the file
warnings = load_warnings()


# Command to issue a warning to a user
@client.tree.command(name="warn", description="Warn a user for a specific reason")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if member.bot:
        await interaction.response.send_message("You cannot warn a bot.", ephemeral=True)
        return

    user_id = str(member.id)  # Store user ID as string for JSON compatibility

    if user_id not in warnings:
        warnings[user_id] = []

    warnings[user_id].append(reason)

    # Save the updated warnings to the file
    save_warnings(warnings)

    # Check if the user has reached 4 warnings
    if len(warnings[user_id]) >= 4:
        try:
            # Kick the user and reset their warnings
            await member.kick(reason="Reached 4 warnings")
            warnings[user_id] = []
            save_warnings(warnings)  # Save the reset warnings
            await interaction.response.send_message(f'{member.mention} has been kicked for reaching 4 warnings.')
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permission to kick this user.", ephemeral=True)
    else:
        await interaction.response.send_message(f'{member.mention} has been warned. Reason: {reason}')
        await member.send(f'You have been warned in {interaction.guild.name} for: {reason}. You have {len(warnings[user_id])} warning(s).')


# Command to view warnings of a user
@client.tree.command(name="warnings", description="View warnings for a user")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def view_warnings(interaction: discord.Interaction, member: discord.Member):
    user_id = str(member.id)
    if user_id in warnings and warnings[user_id]:
        warn_list = '\n'.join([f"{i + 1}. {w}" for i, w in enumerate(warnings[user_id])])
        await interaction.response.send_message(f'{member.mention} has the following warnings:\n{warn_list}')
    else:
        await interaction.response.send_message(f'{member.mention} has no warnings.')


# Command to clear warnings of a user
@client.tree.command(name="clearwarnings", description="Clear all warnings for a user")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def clear_warnings(interaction: discord.Interaction, member: discord.Member):
    user_id = str(member.id)
    if user_id in warnings:
        warnings[user_id] = []
        save_warnings(warnings)  # Save changes to the file
        await interaction.response.send_message(f'Warnings for {member.mention} have been cleared.')
    else:
        await interaction.response.send_message(f'{member.mention} has no warnings to clear.')

# Error handling for missing permissions
@warn.error
@view_warnings.error
@clear_warnings.error
async def permissions_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

client.run(#Insert your bot token here)