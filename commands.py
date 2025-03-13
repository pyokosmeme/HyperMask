# commands.py
import discord
from discord import app_commands
from discord.ext import commands
from utils import log_info, log_error, toggle_verbose, send_large_message
from ai import call_claude
from config import DEFAULT_MODEL
from memory import memory_manager

# Global dictionary to store the last prompt per user for redo functionality.
last_prompts = {}

async def vote_decision(prompt: str, n: int, expected: str, user_id: str, user_data: dict):
    """
    Uses Claude (the cheap model) to decide a yes/no vote.
    Returns True if at least half of n responses include the expected string.
    """
    role = "You are a decision-maker. Answer only with 'yes' or 'no'."
    response = await call_claude(user_id, user_data, DEFAULT_MODEL, role, prompt, 1.0, n, 0, 100, False)
    votes = 0
    for choice in response.choices:
        text = choice["message"]["content"].lower()
        if expected.lower() in text:
            votes += 1
    return votes >= (n / 2)

def setup_commands(bot: commands.Bot, user_data: dict):
    @bot.tree.command(name="info", description="Displays your CatgirlGPT profile and token usage.")
    async def info(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        usage = user_data.get(user_id, {}).get("token_usage", 0)
        await interaction.response.send_message(f"Your total token usage: {usage} tokens.", ephemeral=True)

    @bot.tree.command(name="redo", description="Redo the last answer. Optionally, add extra instructions.")
    async def redo(interaction: discord.Interaction, instructions: str = None):
        user_id = str(interaction.user.id)
        if user_id not in last_prompts:
            await interaction.response.send_message("No previous prompt found to redo.", ephemeral=True)
            return
        extra = instructions if instructions else "Please re-do that answer; do not be vague and be explicit."
        new_prompt = last_prompts[user_id] + "\n" + extra
        # Use the same role prompt as our unified personality
        role = "You are CatgirlGPT, a friendly and adaptive assistant."
        response = await call_claude(user_id, user_data, user_data.get(user_id, {}).get("premium", False) and "claude-3.7-sonnet" or "claude-3-5-haiku", role, new_prompt, 1.0, 1, 0, 1250, False)
        result = response.choices[0]["message"]["content"]
        last_prompts[user_id] = new_prompt
        await interaction.response.send_message(result, ephemeral=True)

    @bot.tree.command(name="verbose", description="Toggle verbose logging (full context sent via DM).")
    async def verbose(interaction: discord.Interaction):
        new_status = toggle_verbose()
        status_text = "enabled" if new_status else "disabled"
        await interaction.response.send_message(f"Verbose logging {status_text}.", ephemeral=True)

    # (You can add additional commands here if needed.)
