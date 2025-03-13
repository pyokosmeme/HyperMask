# utils.py
import discord
import asyncio
import logging

# Setup basic logging
logger = logging.getLogger("CatgirlGPT")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

VERBOSE_LOGGING = False  # Global flag for verbose logging

def log_info(message: str):
    logger.info(message)

def log_error(message: str):
    logger.error(message)

async def send_large_message(channel: discord.TextChannel, message: str, max_length=2000):
    """
    Sends a large message by splitting it into parts.
    """
    if len(message) <= max_length:
        await channel.send(message)
    else:
        parts = []
        while len(message) > max_length:
            split_index = message[:max_length].rfind(" ")
            if split_index == -1:
                split_index = max_length
            parts.append(message[:split_index])
            message = message[split_index:]
        parts.append(message)
        for part in parts:
            await channel.send(part)

def split_msg(msg: str):
    paragraphs = msg.split("\n")
    total_length = sum(len(p) for p in paragraphs)
    half_length = total_length // 2
    cumulative = 0
    index = 0
    for i, p in enumerate(paragraphs):
        cumulative += len(p)
        if cumulative >= half_length:
            index = i
            break
    return "\n".join(paragraphs[:index+1]), "\n".join(paragraphs[index+1:])

def toggle_verbose() -> bool:
    """
    Toggles the global verbose logging flag.
    """
    global VERBOSE_LOGGING
    VERBOSE_LOGGING = not VERBOSE_LOGGING
    return VERBOSE_LOGGING
