# config.py
import os
import json
from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv("/home/inko1nsiderate/catgirlgpt_prod/catgirl.env")

# Discord & Anthropic API tokens and basic settings
DISCORD_TOKEN = os.environ.get("discord_token")
OAI_TOKEN = os.environ.get("oai_token")
BOT_USER_ID = os.environ.get("bot_usr_id")
ALLOWED_SERVERS = json.loads(os.environ.get("allowed_servers", "[]"))
DEFAULT_NAME = os.environ.get("default_name")
DEFAULT_ROLE = os.environ.get("default_role")
LOG_CHANNEL_ID = int(os.environ.get("log_channel"))
XIP_GUILD = os.environ.get("xip")
CATGIRL_APPRECIATOR = os.environ.get("catgirl_appreciator")

# ROLE_IDS as a dictionary
ROLE_IDS = json.loads(os.getenv("ROLE_IDS", "{}"))

# Model selections for Claude:
# Use "claude-3-5-haiku" (cheaper & faster) in place of GPT-3.5‑turbo
# Use "claude-3.7-sonnet" in place of GPT‑4.
DEFAULT_MODEL = "claude-3-5-haiku"
PREMIUM_MODEL = "claude-3.7-sonnet"

# Pricing parameters (dummy values – adjust as needed)
COST_PER_TOKEN_HAIKU = 0.001    # cost per token for claude-3-5-haiku
COST_PER_TOKEN_SONNET = 0.003   # cost per token for claude-3.7-sonnet

# Token limit for our responses (we log usage but do not restrict interaction)
TOKEN_LIMIT = 4000
