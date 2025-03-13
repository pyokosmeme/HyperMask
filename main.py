#!/usr/bin/env python3
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import pickle
import os
import logging

from config import DISCORD_TOKEN, LOG_CHANNEL_ID, ALLOWED_SERVERS, XIP_GUILD, DEFAULT_MODEL, PREMIUM_MODEL
from utils import log_info, log_error, send_large_message
from commands import setup_commands, last_prompts
from ai import call_claude, anthropic_token_count
from memory import memory_manager

# Global dictionary for user data, loaded from file.
user_data = {}
USER_DATA_FILE = "user_info.pickle"

def load_user_data():
    global user_data
    try:
        with open(USER_DATA_FILE, "rb") as f:
            user_data = pickle.load(f)
        log_info("User data loaded successfully.")
    except Exception as e:
        log_error(f"Failed to load user data: {e}")
        user_data = {}

async def save_user_data():
    global user_data
    try:
        with open(USER_DATA_FILE, "wb") as f:
            pickle.dump(user_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        log_error(f"Error saving user data: {e}")

# Set up Discord intents and create the bot instance.
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, description="CatgirlGPT Bot powered by Anthropic Claude.")

# Register our slash commands (which include /redo, /info, /verbose).
setup_commands(bot, user_data)

# Global log channel (set on_ready).
log_channel = None

@bot.event
async def on_ready():
    global log_channel
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send("CatgirlGPT is online!")
    log_info("Bot is ready.")
    # Sync slash commands.
    synced = await bot.tree.sync()
    log_info(f"Synced {len(synced)} slash commands.")
    # Set the bot's presence and update its nickname in all guilds.
    await bot.change_presence(status=discord.Status.online)
    for guild in bot.guilds:
        member = guild.get_member(bot.user.id)
        if member:
            try:
                await member.edit(nick="CatgirlGPT")
            except Exception as e:
                log_error(f"Failed to update nickname in guild {guild.id}: {e}")

@bot.event
async def on_member_join(member: discord.Member):
    user_id = str(member.id)
    if user_id not in user_data:
        user_data[user_id] = {"token_usage": 0, "premium": False}
    await save_user_data()

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    # (Additional subscription update logic can be added here.)
    await save_user_data()

@bot.event
async def on_message(message: discord.Message):
    # Ignore messages from bots.
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if user_id not in user_data:
        user_data[user_id] = {"token_usage": 0, "premium": False}

    # Retrieve a memory summary for the user.
    summary = memory_manager.generate_summary(user_id)
    
    # Define the unified system/personality prompt.
    role_prompt = "You are CatgirlGPT, a friendly and adaptive assistant with a playful personality."
    
    # Build the full prompt: include the memory summary and the new message,
    # labeling the user’s turn with "Senpai:".
    content = message.clean_content
    full_prompt = f"{summary}\nSenpai: {content}"
    # Store the prompt for potential redo.
    last_prompts[user_id] = full_prompt

    # Select the model based on whether the user is premium.
    model_to_use = PREMIUM_MODEL if user_data[user_id].get("premium", False) else DEFAULT_MODEL

    # Call the Claude API while simulating typing.
    async with message.channel.typing():
        response = await call_claude(user_id, user_data, model_to_use, role_prompt, full_prompt, 1.0, 1, 0, 1250, False)
    result = response.choices[0].message["content"]

    # Update memory with this interaction.
    memory_manager.add_event(user_id, f"Senpai said: {content}")
    from config import DEFAULT_NAME
    memory_manager.add_event(user_id, f"{DEFAULT_NAME} replied: {result}")

    # Log token usage; if usage is very high, log a warning.
    if user_data[user_id]["token_usage"] > 100000:
        log_error(f"Warning: High token usage for user {user_id}")

    # Send the response back to Discord.
    await send_large_message(message.channel, f"{message.author.mention} {result}", max_length=2000)
    await save_user_data()

# Periodically save user data every minute.
@tasks.loop(minutes=1)
async def periodic_save():
    await save_user_data()

@periodic_save.before_loop
async def before_periodic_save():
    await bot.wait_until_ready()

periodic_save.start()

# Load user data from file.
load_user_data()

bot.run(DISCORD_TOKEN)
