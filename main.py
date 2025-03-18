#!/usr/bin/env python3
import discord
from discord.ext import commands, tasks
import pickle
import os
import logging
import aiofiles
import re
import asyncio

from config import (
    DISCORD_TOKEN,
    DEFAULT_NAME,
    LOG_CHANNEL_ID,
    DEFAULT_MODEL,
    PREMIUM_MODEL,
    CORE_PROMPT
)
from utils import log_info, log_error, send_large_message
from commands import setup_commands
from ai import call_claude
from memory import maybe_summarize_conversation

# Global counter for bot replies.
bot_reply_counts = {}
BOT_REPLY_THRESHOLD = 1  # Adjust threshold as needed.

# Async lock for accessing bot_reply_counts.
bot_reply_lock = asyncio.Lock()

# Global dictionary to store channel context for public channels.
# Key: channel ID, Value: list of messages (each as a dict with author and content)
channel_context = {}


# Function to build external context based on total character length.
def build_external_context(channel_id):
    messages = channel_context.get(channel_id, [])
    # Start from the most recent message and work backwards.
    selected_msgs = []
    total_chars = 0
    # Reverse the list so we add most recent messages first.
    for msg in reversed(messages):
        msg_len = len(msg["content"])
        if total_chars + msg_len > 6000: # ~ 2000 tokens
            break
        selected_msgs.insert(0, f"{msg['author']}: {msg['content']}")
        total_chars += msg_len
    return "\n".join(selected_msgs)
    
async def get_yes_no_votes(message, external_context="", is_bot=False, vote_count=3):
    votes = []
    # Define the prompt first
    bot_name = DEFAULT_NAME  # from config
    penalty_text = ""
    if is_bot:
        async with bot_reply_lock:
            count = bot_reply_counts.get(message.author.id, 0)
        penalty_text = f" Note: this message is from a bot and you have already received {count} replies from me. Bot Reply Threshold is set at {BOT_REPLY_THRESHOLD}"
    
    prompt = f"""[System Addenum, OOC]: {bot_name}, below is the ongoing conversational context, and above is a message that was sent to an LLM, and 
    you are tasked with something quite simple and straightforward. Given the existing conversational context, respond with a simple yes/no: would you like to reply to this message? 
    Only respond with either yes, or no. No commentary or follow-up questions about the context. 
    Respond with only the word 'Yes' or 'No' without any additional text, explanation, punctuation or commentary. 
    Just the single word answer alone {penalty_text}.\n External Context: \n {external_context}"""
    
    dummy_user_dict = {
        "system_vote": {
            "token_usage": 0,
            "premium": False,
            "conversation_history": [
                {"role": "user", "content": "dummy conversation message to satisfy API requirements."}
            ]
        }
    }

    for _ in range(vote_count):
        try:
            response = await call_claude(
                user_id="system_vote",
                user_dict=dummy_user_dict,
                model="claude-3-5-haiku-20241022",
                system_prompt=prompt,
                user_content=message.clean_content,
                temperature=1.0,
                max_tokens=5,
                verbose=False
            )
            vote_raw = response.choices[0].message["content"].strip().lower()
            if "yes" in vote_raw:
                votes.append("yes")
            elif "no" in vote_raw:
                votes.append("no")
            else:
                votes.append("abstain")
        except Exception as e:
            log_error(f"Error getting vote: {e}")
            votes.append("abstain")  # Default to abstain on error
            
    return votes

async def should_reply(message):
    if isinstance(message.channel, discord.DMChannel):
        return True

    bot_name = DEFAULT_NAME
    if re.search(bot_name, message.clean_content, re.IGNORECASE):
        return True

    if message.author.bot:
        async with bot_reply_lock:
            count = bot_reply_counts.get(message.author.id, 0)
            if count >= BOT_REPLY_THRESHOLD:
                return False

    is_bot_message = message.author.bot
    external_context = ""
    # Only build external context for public channels.
    if not isinstance(message.channel, discord.DMChannel):
        external_context = build_external_context(message.channel.id)

    votes = await get_yes_no_votes(message, external_context, is_bot=is_bot_message, vote_count=3)
    yes_votes = votes.count("yes")
    no_votes = votes.count("no")
    abstain_votes = votes.count("abstain")
    return yes_votes > no_votes and yes_votes > abstain_votes


user_data = {}
USER_DATA_FILE = "user_info.pickle"

async def load_user_data():
    global user_data
    try:
        async with aiofiles.open(USER_DATA_FILE, "rb") as f:
            data = await f.read()
            loaded_data = pickle.loads(data)
            user_data.clear()
            user_data.update(loaded_data)
        log_info("User data loaded successfully.")
    except (pickle.PickleError, EOFError) as e:
        log_error(f"Corrupted user data file: {e}")
        # Try to load from backup if it exists
        try:
            if os.path.exists(f"{USER_DATA_FILE}.bak"):
                async with aiofiles.open(f"{USER_DATA_FILE}.bak", "rb") as f:
                    data = await f.read()
                    loaded_data = pickle.loads(data)
                    user_data.clear()
                    user_data.update(loaded_data)
                log_info("User data loaded from backup successfully.")
            else:
                user_data.clear()
        except Exception as backup_e:
            log_error(f"Failed to load backup: {backup_e}")
            user_data.clear()
    except Exception as e:
        log_error(f"Failed to load user data: {e}")
        user_data.clear()

async def save_user_data():
    global user_data
    try:
        # First, check if the current file exists and create backup
        if os.path.exists(USER_DATA_FILE):
            try:
                # Read the current file
                async with aiofiles.open(USER_DATA_FILE, "rb") as current_file:
                    current_data = await current_file.read()
                
                # Write it to the backup location
                async with aiofiles.open(f"{USER_DATA_FILE}.bak", "wb") as backup_file:
                    await backup_file.write(current_data)
                
                log_info("Created backup of user data")
            except Exception as backup_e:
                log_error(f"Failed to create backup: {backup_e}")
        
        # Now save the current data
        async with aiofiles.open(USER_DATA_FILE, "wb") as f:
            await f.write(pickle.dumps(user_data, protocol=pickle.HIGHEST_PROTOCOL))
        
        log_info("User data saved successfully")
    except Exception as e:
        log_error(f"Error saving user data: {e}")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, description="A Claude based persona.")

setup_commands(bot, user_data)

@bot.event
async def on_ready():
    global log_channel
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        # Startup message includes DEFAULT_NAME in parentheses.
        await log_channel.send(f"Claude's Mask ({DEFAULT_NAME}) is online!")
        await log_channel.send("Loading user data...")
    try:
        await load_user_data()
        if log_channel:
            await log_channel.send("User data loaded successfully!")
    except Exception as e:
        if log_channel:
            await log_channel.send(f"Error loading user data: {e}")
    log_info("Claude's Mask is online!")

    synced = await bot.tree.sync()
    log_info(f"Synced {len(synced)} slash commands.")
    await bot.change_presence(status=discord.Status.online)

    for guild in bot.guilds:
        member = guild.get_member(bot.user.id)
        if member:
            try:
                await member.edit(nick=f"{DEFAULT_NAME}")
            except Exception as e:
                log_error(f"Failed to update nickname in guild {guild.id}: {e}")

    # Only start periodic_save if it's not already running
    if not periodic_save.is_running():
        periodic_save.start()

@bot.event
async def on_member_join(member: discord.Member):
    user_id = str(member.id)
    if user_id not in user_data:
        user_data[user_id] = {
            "token_usage": 0,
            "premium": False,
            "conversation_history": [],
            "core_memories": ""
        }
    await save_user_data()

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    await save_user_data()

@bot.event
async def on_message(message: discord.Message):
    # Skip processing the bot's own messages.
    if message.author.id == bot.user.id:
        return

    # For public channels, record messages for external context.
    if not isinstance(message.channel, discord.DMChannel):
        channel_context.setdefault(message.channel.id, [])
        clean_content = message.clean_content.strip()
        if clean_content:
            channel_context[message.channel.id].append({
                "author": message.author.name,
                "content": clean_content
            })
        # Instead of limiting to last 20 messages, you could also prune the list if needed:
        if len(channel_context[message.channel.id]) > 100:  # e.g., keep at most 100 messages.
            channel_context[message.channel.id] = channel_context[message.channel.id][-100:]

    # Handle admin commands in the log channel.
    if message.channel.id == log_channel.id:
        if message.author.bot:
            return
        split = message.content.split()
        if not split:
            return
        cmd = split[0].lower()
        # Shutdown command now must be: "shutdown? {DEFAULT_NAME}"
        if cmd == "shutdown?":
            if len(split) > 1 and split[1].lower() == DEFAULT_NAME.lower():
                await log_channel.send(
                    f"Admin {message.author.name}[id:{message.author.id}] sent shutdown? {DEFAULT_NAME}. Shutting down ({DEFAULT_NAME})..."
                )
                await log_channel.send(f"***Shutting down Claude's Mask ({DEFAULT_NAME})***")
                await bot.change_presence(status=discord.Status.invisible)
                await bot.close()
                return
            else:
                await log_channel.send(f"Invalid shutdown command. Use: shutdown? {DEFAULT_NAME}")
                return
        elif cmd == "user" and len(split) > 1 and split[1].lower() == "data?":
            if len(split) > 2:
                target_user_id = split[2]
                data = user_data.get(target_user_id)
                if data:
                    msg = f"User data for {target_user_id}:\n```{data}```"
                    await send_large_message(log_channel, msg)
                else:
                    await send_large_message(log_channel, f"No data found for user {target_user_id}.")
            else:
                await send_large_message(log_channel, "Usage: user data? [user_id]")
            return

    # For non-DM messages, check if we should reply.
    if not isinstance(message.channel, discord.DMChannel):
        if not await should_reply(message):
            return

    # Get the clean message content and skip if empty.
    content = message.clean_content.strip()
    if not content:
        return

    # Reset or update bot reply counts.
    if not message.author.bot:
        async with bot_reply_lock:
            bot_reply_counts.clear()
    else:
        async with bot_reply_lock:
            count = bot_reply_counts.get(message.author.id, 0)
            if count >= BOT_REPLY_THRESHOLD:
                return
            bot_reply_counts[message.author.id] = count + 1

    user_id = str(message.author.id)
    # Initialize user data if not already present.
    if user_id not in user_data:
        user_data[user_id] = {
            "token_usage": 0,
            "premium": False,
            "dm_conversation_history": [],
            "public_conversation_history": [],
            "core_memories": "",
            # Legacy combined history for backward compatibility.
            "conversation_history": []
        }
    else:
        # Migrate old combined history if needed.
        if "dm_conversation_history" not in user_data[user_id]:
            user_data[user_id]["dm_conversation_history"] = user_data[user_id].get("conversation_history", [])
        if "public_conversation_history" not in user_data[user_id]:
            user_data[user_id]["public_conversation_history"] = []

    # Append the incoming message to the appropriate separate history.
    if isinstance(message.channel, discord.DMChannel):
        user_data[user_id]["dm_conversation_history"].append({"role": "user", "content": content})
        selected_history = user_data[user_id]["dm_conversation_history"]
        extra_context = "This is a private conversation. You may be casual, personal, and more intimate."
        external_context = ""
    else:
        user_data[user_id]["public_conversation_history"].append({"role": "user", "content": content})
        selected_history = user_data[user_id]["public_conversation_history"]
        extra_context = (
            "This is a public channel. Be yourself, but the conversation is public; "
            "be aware not to carry over private conversation topics unless you want everyone to know about them."
        )
        # Use the new function to build context based on total character length.
        external_context = build_external_context(message.channel.id)

    # For compatibility with existing functions (call_claude, maybe_summarize_conversation),
    # update the legacy combined history to use the selected history.
    user_data[user_id]["conversation_history"] = selected_history

    # Summarize if necessary.
    await maybe_summarize_conversation(user_id, user_data)

    # Build the system prompt.
    core_mem = user_data[user_id].get("core_memories", "")
    system_text = f"{extra_context}\n"
    if external_context:
        system_text += f"External Context:\n{external_context}\n"
    system_text += f"{CORE_PROMPT}\n\nCore Memories:\n{core_mem}"
    if message.author.bot:
        system_text += "\n[IMPORTANT: The person you're responding to tends to engage in lengthy exchanges. Keep your response concise (50-100 words maximum). Be direct and to the point while maintaining your character. Minimize questions. A brief, meaningful response will encourage a more balanced conversation.]"

    model_to_use = PREMIUM_MODEL if user_data[user_id].get("premium", False) else DEFAULT_MODEL

    async with message.channel.typing():
        response = await call_claude(
            user_id=user_id,
            user_dict=user_data,
            model=model_to_use,
            system_prompt=system_text,
            user_content=None,
            temperature=1.0,
            max_tokens=1250,
            verbose=False
        )
        # For bot messages, calculate a delay proportional to the length of the reply.
        # Default is 5 ms per character.
        if message.author.bot:
            delay_time = len(message.content)*0.05
            await asyncio.sleep(delay_time)
    result = response.choices[0].message["content"]

    # Append the assistant's reply to the appropriate separate history.
    reply_entry = {"role": "assistant", "content": result}
    if isinstance(message.channel, discord.DMChannel):
        user_data[user_id]["dm_conversation_history"].append(reply_entry)
    else:
        user_data[user_id]["public_conversation_history"].append(reply_entry)
    # Update the legacy combined history as well.
    user_data[user_id]["conversation_history"] = selected_history

    await send_large_message(message.channel, f"{message.author.mention} {result}")
    await save_user_data()
    await bot.process_commands(message)


@tasks.loop(minutes=1)
async def periodic_save():
    await save_user_data()

@periodic_save.before_loop
async def before_periodic_save():
    await bot.wait_until_ready()

bot.run(DISCORD_TOKEN)
