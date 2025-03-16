# config.py
import os
import json
from dotenv import load_dotenv

load_dotenv("config.env")

# Use a valid Anthropic API key. If you set your environment variable as ANTHROPIC_API_KEY,
# you can have the client auto-detect it; otherwise, we pass it explicitly.
OAI_TOKEN = os.environ.get("ANTHROPIC_API_KEY")  # Alternatively, set this to your key string

DISCORD_TOKEN = os.environ.get("discord_token")
LOG_CHANNEL_ID = int(os.environ.get("log_channel", "0"))

# Model names – adjust these as needed.

DEFAULT_MODEL = "claude-3-7-sonnet-latest"
PREMIUM_MODEL = "claude-3-7-sonnet-latest"

# Example token cost per token (adjust to your real pricing)
COST_PER_TOKEN_HAIKU = 0.0000008
COST_PER_TOKEN_SONNET = 0.000003

# Persona/system prompt for your bot
CORE_PROMPT = os.environ.get("core_prompt", "You are CatgirlGPT, a friendly and adaptive assistant.")
DEFAULT_NAME = os.environ.get("default_name", "Theia")

# Summarizer system prompt used when summarizing conversation for core memory updates
SUMMARIZATION_PROMPT = os.environ.get("summarization_prompt", "You are a summarizer. Please update core memories and provide a short summary.")

CORE_MEMORY_PROMPT = os.environ.get("core_memory_prompt", "Update core memories based on the conversation below.")

CORE_MEMORY_DUMP_PROMPT = os.environ.get("core_memory_dump", "Update core memories based on the conversation below.")

ENABLE_CORE_MEMORY_PICKLE_LOG = True  # Toggle for logging core memories.
CORE_MEMORY_PICKLE_DIR = "./"         # Directory to save the pickle files.

ENABLE_API_CALL_LOGGING = False  # Set to True to enable logging, False to disable
