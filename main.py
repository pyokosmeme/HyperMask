# main.py
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import pickle
import json
import os
import logging

from config import DISCORD_TOKEN, LOG_CHANNEL_ID, ALLOWED_SERVERS, XIP_GUILD, DEFAULT_MODEL, PREMIUM_MODEL, TOKEN_LIMIT
from utils import log_info, log_error, send_large_message
from commands import setup_commands, last_prompts
from ai import call_claude, anthropic_token_count
from memory import memory_manager

# Global dictionary for user data; load from file if available.
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

# Setup Discord intents and bot instance.
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, description="CatgirlGPT Bot powered by Anthropic Claude.")

# Register slash commands.
setup_commands(bot, user_data)

# Global log channel (to be set on_ready).
log_channel = None

@bot.event
async def on_ready():
    global log_channel
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send("CatgirlGPT is online!")
    log_info("Bot is ready.")
    synced = await bot.tree.sync()
    log_info(f"Synced {len(synced)} slash commands.")
    # Set a default presence and update nickname in all guilds.
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
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if user_id not in user_data:
        user_data[user_id] = {"token_usage": 0, "premium": False}

    # Retrieve the memory summary for this user.
    summary, deep = memory_manager.get_full_memory(user_id)

    # Our unified personality role prompt.
    role_prompt = "You are CatgirlGPT, a friendly and adaptive assistant with a playful personality."

    # Build the full prompt to send to Claude.
    content = message.clean_content
    full_prompt = f"{summary}\nUser: {content}"
    last_prompts[user_id] = full_prompt  # store for potential redo

    # Select the model based on user premium status.
    model_to_use = PREMIUM_MODEL if user_data[user_id].get("premium", False) else DEFAULT_MODEL

    # Use verbose mode if enabled (global flag from utils)
    from utils import VERBOSE_LOGGING
    verbose = VERBOSE_LOGGING

    # Simulate typing while processing.
    async with message.channel.typing():
        response = await call_claude(user_id, user_data, model_to_use, role_prompt, full_prompt, 1.0, 1, 0, 1250, False, verbose=verbose)

    result = response.choices[0]["message"]["content"]

    # Update memory manager with both the user’s message and the bot’s reply.
    memory_manager.add_event(user_id, f"User said: {content}")
    memory_manager.add_event(user_id, f"CatgirlGPT replied: {result}")

    # Log token usage and, if usage is very high in a short time, log a warning.
    if user_data[user_id]["token_usage"] > 100000:
        log_error(f"Warning: High token usage for user {user_id}")

    await send_large_message(message.channel, f"{message.author.mention} {result}", max_length=2000)
    await save_user_data()

@bot.event
async def on_member_update(before, after):
    # (Update subscription details if needed; here we simply save data.)
    await save_user_data()

# Periodically save user data (every minute)
@tasks.loop(minutes=1)
async def periodic_save():
    await save_user_data()

@periodic_save.before_loop
async def before_periodic_save():
    await bot.wait_until_ready()

periodic_save.start()

# Load user data on startup.
load_user_data()

bot.run(DISCORD_TOKEN)
