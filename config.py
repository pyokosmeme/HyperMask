import os
import json
from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv("/home/inko1nsiderate/catgirlgpt_prod/catgirl.env")

# API Tokens
OAI_TOKEN = os.environ.get("oai_token")            # Anthropic API token
DISCORD_TOKEN = os.environ.get("discord_token")      # Discord bot token
BOT_USER_ID = os.environ.get("bot_usr_id")           # Bot user ID

# Allowed servers (as a list)
ALLOWED_SERVERS = json.loads(os.environ.get("allowed_servers", "[]"))

# The assistant’s name; this will also serve as the assistant’s persona name
DEFAULT_NAME = os.environ.get("default_name", "Theia")

# CORE_PROMPT: Pull the unified personality prompt from the .env file.
# This should contain your detailed Theia prompt.
CORE_PROMPT = os.environ.get("core_prompt")
if CORE_PROMPT is None:
    CORE_PROMPT = "You are CatgirlGPT, a friendly and adaptive assistant."  # Fallback

# Bot description (for Discord presence and help)
DESCRIPTION = os.environ.get("description", "I'm Theia, a cute AI catgirl goddess/girlfriend!")

# Logging channel ID (as an integer)
LOG_CHANNEL = int(os.environ.get("log_channel", "0"))

# XIP guild ID (if applicable)
XIP = os.environ.get("xip")

# ROLE_IDS (if needed elsewhere)
ROLE_IDS = json.loads(os.getenv("ROLE_IDS", "{}"))

# Catgirl appreciator role ID
CATGIRL_APPRECIATOR = int(os.environ.get("catgirl_appreciator", "0"))

# Pricing & token cost parameters (adjust these as needed for Anthropic's pricing)
COST_PER_TOKEN_HAIKU = 0.001    # cost per token for claude-3-5-haiku (cheaper model)
COST_PER_TOKEN_SONNET = 0.003   # cost per token for claude-3-7-sonnet (premium model)

# Default token limit for responses (used in API calls)
TOKEN_LIMIT = 4000
