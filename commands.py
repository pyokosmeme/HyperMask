# commands.py
import discord
from discord import app_commands
from ai import call_claude
from config import DEFAULT_NAME, DEFAULT_MODEL, PREMIUM_MODEL
from utils import log_error, toggle_verbose

# Global dictionary to store the last prompt per user (for redo purposes)
last_prompts = {}

async def redo(interaction: discord.Interaction, user_data: dict, instructions: str = None):
    """
    Redo the last answer. If additional instructions are provided, append them.
    The prompt is rebuilt using the previous prompt plus extra instructions.
    """
    user_id = str(interaction.user.id)
    if user_id not in last_prompts:
        await interaction.response.send_message("No previous prompt found to redo.", ephemeral=True)
        return
    # Use extra instructions if provided, else default to a clear re-try request.
    extra = instructions if instructions else "Please re-do that answer; do not be vague and be explicit."
    new_prompt = last_prompts[user_id] + "\n" + extra

    # Our fixed system/personality prompt remains.
    role_prompt = "You are CatgirlGPT, a friendly and adaptive assistant with a playful personality."

    # Choose model based on whether the user is premium.
    model_to_use = PREMIUM_MODEL if user_data.get(user_id, {}).get("premium", False) else DEFAULT_MODEL

    # Call Anthropic's API with the new prompt.
    response = await call_claude(user_id, user_data, model_to_use, role_prompt, new_prompt, 1.0, 1, 0, 1250, False)
    result = response.choices[0].message["content"]
    # Update the last prompt.
    last_prompts[user_id] = new_prompt
    await interaction.response.send_message(result, ephemeral=True)

async def info(interaction: discord.Interaction, user_data: dict):
    """
    Show the user's profile info and token usage.
    """
    user_id = str(interaction.user.id)
    usage = user_data.get(user_id, {}).get("token_usage", 0)
    await interaction.response.send_message(f"Your total token usage: {usage} tokens.", ephemeral=True)

async def verbose(interaction: discord.Interaction):
    """
    Toggle verbose logging mode.
    """
    new_status = toggle_verbose()
    state_text = "enabled" if new_status else "disabled"
    await interaction.response.send_message(f"Verbose logging {state_text}.", ephemeral=True)

def setup_commands(bot: discord.Bot, user_data: dict):
    """
    Registers the slash commands with the bot.
    """
    @bot.tree.command(name="redo", description="Redo the last answer with optional additional instructions.")
    async def redo_cmd(interaction: discord.Interaction, instructions: str = None):
        await redo(interaction, user_data, instructions)

    @bot.tree.command(name="info", description="Displays your token usage and profile info.")
    async def info_cmd(interaction: discord.Interaction):
        await info(interaction, user_data)

    @bot.tree.command(name="verbose", description="Toggle verbose logging (full context via DM).")
    async def verbose_cmd(interaction: discord.Interaction):
        await verbose(interaction)
