import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from config import DEFAULT_MODEL, PREMIUM_MODEL, CORE_PROMPT
from utils import log_error, toggle_verbose
from ai import call_claude  # Import needed for reroll

# Global dictionary to track active reroll views by user ID.
active_reroll_views = {}

def disable_previous_views(user_id: str):
    if user_id in active_reroll_views:
        for view in active_reroll_views[user_id]:
            for child in view.children:
                child.disabled = True
            view.stop()
        active_reroll_views[user_id] = []

class RerollView(View):
    def __init__(self, result: str, user_id: str, system_text: str, model: str, temp_user_data: dict, reroll_callback, original_message: discord.Message):
        """
        :param result: The initial rerolled output.
        :param user_id: The ID of the user invoking reroll.
        :param system_text: The system prompt built for the LLM call.
        :param model: The model to use.
        :param temp_user_data: The temporary user data for the LLM call.
        :param reroll_callback: Callback function to re-run the reroll logic.
        :param original_message: The ephemeral message sent initially.
        """
        super().__init__(timeout=60)
        self.result = result
        self.user_id = user_id
        self.system_text = system_text
        self.model = model
        self.temp_user_data = temp_user_data
        self.reroll_callback = reroll_callback
        self.original_message = original_message

    async def disable_buttons(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        self.stop()
        try:
            await self.original_message.edit(view=self)
        except discord.NotFound:
            pass

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Accept: update the ephemeral message and then send result publicly.
        await self.original_message.edit(content="Message accepted.")
        await interaction.response.send_message(f"{self.result}")
        self.stop()
        if self.user_id in active_reroll_views and self in active_reroll_views[self.user_id]:
            active_reroll_views[self.user_id].remove(self)

    @discord.ui.button(label="Dismiss", style=discord.ButtonStyle.danger, emoji="❌")
    async def dismiss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Dismiss: update the ephemeral message.
        await self.original_message.edit(content="Reroll dismissed.")
        self.stop()
        if self.user_id in active_reroll_views and self in active_reroll_views[self.user_id]:
            active_reroll_views[self.user_id].remove(self)

    @discord.ui.button(label="Redo", style=discord.ButtonStyle.primary, emoji="🎲")
    async def redo_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable current view's buttons
        for child in self.children:
            child.disabled = True
        try:
            await self.original_message.edit(view=self)
        except discord.NotFound:
            await interaction.response.send_message("The original message was deleted. Please try again.",
                                                    ephemeral=True)
            return
        except discord.HTTPException as e:
            log_error(f"Error updating message: {e}")
            await interaction.response.send_message("Failed to update the message. Please try again.", ephemeral=True)
            return

        # Add a deferred response while we wait for the reroll
        await interaction.response.defer(ephemeral=True)

        # Re-run the reroll callback
        try:
            new_result = await self.reroll_callback(self.user_id, self.system_text, self.model, self.temp_user_data)
            self.result = new_result
        except Exception as e:
            log_error(f"Error during reroll: {e}")
            await interaction.followup.send("An error occurred during reroll. Please try again.", ephemeral=True)
            return

        # Create a new view instance with fresh buttons
        new_view = RerollView(
            result=new_result,
            user_id=self.user_id,
            system_text=self.system_text,
            model=self.model,
            temp_user_data=self.temp_user_data,
            reroll_callback=self.reroll_callback,
            original_message=self.original_message
        )

        # Disable previous views for this user
        disable_previous_views(self.user_id)
        active_reroll_views.setdefault(self.user_id, []).append(new_view)

        # Edit the original ephemeral message with the new result and view
        try:
            await self.original_message.edit(content=new_result, view=new_view)
            await interaction.followup.send("Reroll complete!", ephemeral=True)
        except discord.HTTPException as e:
            log_error(f"Error updating message with reroll: {e}")
            await interaction.followup.send("Failed to update the message with the new response. Please try again.",
                                            ephemeral=True)



def setup_commands(bot: commands.Bot, user_data: dict):
    
    @bot.tree.command(name="forget", description="Reset your conversation history with the bot.")
    async def forget(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id not in user_data:
            await interaction.response.send_message("No conversation history found.", ephemeral=True)
            return

        # Keep core memories but clear conversation history
        user_data[user_id]["conversation_history"] = []
        await interaction.response.send_message(
            "Your conversation history has been reset. Core memories remain intact.", ephemeral=True)

    @bot.tree.command(name="remember", description="Add a custom memory to the bot's knowledge about you.")
    @app_commands.describe(memory="The memory you want to add")
    async def remember(interaction: discord.Interaction, memory: str):
        user_id = str(interaction.user.id)
        if user_id not in user_data:
            user_data[user_id] = {
                "token_usage": 0,
                "premium": False,
                "conversation_history": [],
                "core_memories": ""
            }

        # Add the memory to core memories
        current_memories = user_data[user_id].get("core_memories", "")
        user_data[user_id]["core_memories"] = f"{current_memories}\n- {memory}"

        await interaction.response.send_message("I'll remember that.", ephemeral=True)

    @bot.tree.command(name="status", description="Check your status with the bot.")
    async def status(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id not in user_data:
            await interaction.response.send_message("No data found for you.", ephemeral=True)
            return

        token_usage = user_data[user_id].get("token_usage", 0)
        premium_status = "Premium" if user_data[user_id].get("premium", False) else "Standard"
        conversation_length = len(user_data[user_id].get("conversation_history", []))

        await interaction.response.send_message(
            f"Status:\n"
            f"- Plan: {premium_status}\n"
            f"- Token usage: {token_usage:,} tokens\n"
            f"- Conversation length: {conversation_length} messages\n"
            f"- Core memories: {len(user_data[user_id].get('core_memories', '').split('\\n'))} entries",
            ephemeral=True
        )

    @bot.tree.command(name="help", description="Get help with bot commands.")
    async def help_command(interaction: discord.Interaction):
        commands_list = [
            ("forget", "Reset your conversation history"),
            ("remember", "Add a custom memory"),
            ("reroll", "Get a different response to your last message"),
            ("status", "Check your usage statistics"),
            ("debug", "Toggle verbose logging or view conversation"),
            ("help", "Show this help message")
        ]

        help_text = "Available Commands:\n" + "\n".join([f"/{cmd} - {desc}" for cmd, desc in commands_list])

        await interaction.response.send_message(help_text, ephemeral=True)

    @bot.tree.command(name="debug", description="Toggle verbose logging and/or show the conversation.")
    @app_commands.describe(action="What do you want to do? 'toggle' verbose logging, 'show' conversation, or 'both'?")
    async def debug(interaction: discord.Interaction, action: str):
        user_id = str(interaction.user.id)
        if action.lower() in ["toggle", "both"]:
            new_status = toggle_verbose()
            state_text = "enabled" if new_status else "disabled"
            await interaction.response.send_message(f"Verbose logging {state_text}.", ephemeral=True)
        if action.lower() in ["show", "both"]:
            context = user_data.get(user_id, {}).get("conversation_history", [])
            if not context:
                await interaction.followup.send("No conversation context available.", ephemeral=True)
                return
            context_str = "\n".join(f"{msg['role']}: {msg['content']}" for msg in context)
            try:
                await interaction.user.send(f"Full Conversation Context:\n{context_str}")
                await interaction.followup.send("I've DM'd you the full conversation context.", ephemeral=True)
            except Exception:
                await interaction.followup.send("Failed to send DM. Check your DM settings.", ephemeral=True)

    @bot.tree.command(name="reroll", description="Reroll the last assistant response with optional additional context.")
    @app_commands.describe(context="Additional context to include (optional).")
    async def reroll(interaction: discord.Interaction, context: str = None):
        user_id = str(interaction.user.id)
        conv_history = user_data.get(user_id, {}).get("conversation_history", [])
        if not conv_history:
            await interaction.response.send_message("No conversation history available to reroll.", ephemeral=True)
            return

        # Remove the last assistant message if it exists.
        if conv_history[-1]["role"] == "assistant":
            temp_history = conv_history[:-1]
        else:
            temp_history = conv_history[:]

        if context:
            temp_history.append({
                "role": "user",
                "content": "[OOC]: " + context + "\nIf you respond to this context, please use [OOC] tags."
            })

        core_mem = user_data[user_id].get("core_memories", "")
        system_text = f"{CORE_PROMPT}\n\nCore Memories:\n{core_mem}"
        model = PREMIUM_MODEL if user_data[user_id].get("premium", False) else DEFAULT_MODEL

        temp_user_data = {
            user_id: {
                "conversation_history": temp_history,
                "core_memories": core_mem,
                "premium": user_data[user_id].get("premium", False)
            }
        }

        # Define the reroll callback for the "Redo" functionality.
        async def reroll_callback(user_id: str, system_text: str, model: str, temp_user_data: dict) -> str:
            async with interaction.channel.typing():
                new_response = await call_claude(
                    user_id=user_id,
                    user_dict=temp_user_data,
                    model=model,
                    system_prompt=system_text,
                    user_content=None,
                    temperature=1.0,
                    max_tokens=1250,
                    verbose=False
                )
            return new_response.choices[0].message["content"]

        # Before processing this reroll, disable any previous active reroll views for this user.
        disable_previous_views(user_id)

        # Defer the response and call the LLM.
        await interaction.response.defer(ephemeral=True)
        async with interaction.channel.typing():
            response = await call_claude(
                user_id=user_id,
                user_dict=temp_user_data,
                model=model,
                system_prompt=system_text,
                user_content=None,
                temperature=1.0,
                max_tokens=1250,
                verbose=False
            )
        result = response.choices[0].message["content"]

        # Send the ephemeral message and get its message object.
        ephemeral_msg = await interaction.followup.send(content=result, ephemeral=True)
        # Create a view instance with the original ephemeral message.
        new_view = RerollView(
            result=result,
            user_id=user_id,
            system_text=system_text,
            model=model,
            temp_user_data=temp_user_data,
            reroll_callback=reroll_callback,
            original_message=ephemeral_msg
        )
        # Register the new view in our active views.
        active_reroll_views.setdefault(user_id, []).append(new_view)
        # Edit the ephemeral message to add the view.
        await ephemeral_msg.edit(view=new_view)
