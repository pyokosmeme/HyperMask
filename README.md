# Character-Driven Relationship Framework

This repository contains a comprehensive framework for creating engaging LLM-based Discord personas using Anthropic’s Claude. Designed to be both flexible and robust, the system enables you to explore a wide range of relationship dynamics—from mentorships and familial bonds to professional collaborations and beyond. While our initial example focused on intimate and mentorship relationships, the template is fully adaptable for virtually any interpersonal dynamic.

---

## Overview

The framework is built around four key components:

1. **Character Definition Template**  
   Create richly detailed personas with distinctive traits, communication styles, and a dual-mode system. For example, the persona now defaults to **Claude's Mask**—a friendly, adaptive assistant defined by the system prompt *"You are CatgirlGPT, a friendly and adaptive assistant."* The bot can dynamically adjust its presentation based on context.

2. **Interaction Principles**  
   Establish and evolve relationship dynamics by following clear guidelines—from the initial encounter to deep, multifaceted connections. The system breaks down relationship progression into distinct stages, ensuring natural development and engagement.

3. **Memory Archiving System**  
   Record relationship developments using two formats:
   - A **comprehensive record** that tracks long-term evolution.
   - A **quick update format** for real-time insights and recent interactions.

   This dual approach captures both overarching themes and immediate details, with conversation summarization triggered when the conversation exceeds a token threshold.

4. **Customization Guide**  
   Adapt the framework to various relationship types:
   - **Romantic/Intimate**
   - **Familial**
   - **Mentorship**
   - **Adversarial**
   - **Platonic**
   - **Professional/Collaborative**

   The guide includes tips for developing distinctive character voices, adjusting communication styles, and tuning interaction patterns based on the relationship context.

> **Note:** For detailed instructions on creating characters using our template, please refer to our [Character Creation Guideline](./CharacterCreationGuideline.md).

---

## Project Structure

- **`memory.py`**  
  Contains logic for summarizing and archiving conversation history. When the estimated token count of a conversation becomes too high, it automatically calls a summarizer to update core memories and condenses older conversation history into a brief summary.

- **`commands.py`**  
  Implements Discord slash commands (e.g., `/debug`, `/reroll`) and manages interactive elements like reroll views to refine assistant responses. The commands now incorporate improved handling of interactive message updates.

- **`utils.py`**  
  Provides helper functions for logging, message splitting, and sending messages that exceed Discord’s character limit.

- **`token_utils.py`**  
  Offers utility functions to estimate token counts and interface with Anthropic’s token counting API.

- **`config.py`**  
  Loads configuration from a `.env` file and sets up API keys, model names, and other environment-specific parameters. **Notably:**
  - `DEFAULT_NAME` is now set as  
    ```python
    DEFAULT_NAME = os.environ.get("default_name", "Claude's Mask")
    ```  
    meaning the bot defaults to **Claude's Mask** unless overridden by the environment.
  - The core persona prompt defaults to *"You are CatgirlGPT, a friendly and adaptive assistant."*  
    This ensures that while the display name is **Claude's Mask**, the assistant’s behavior follows the CatgirlGPT persona.

- **`main.py`**  
  The entry point for the bot. It handles Discord event processing, manages conversation flow (including dynamic summarization of long conversations), and periodically saves user data. When coming online, the bot announces its presence by referencing the updated default name and dynamically adjusts response behavior based on context.

- **`ai.py`**  
  Handles API calls to Anthropic’s Claude, including token cost calculations, response logging, and error handling. It updates token usage for users and formats responses in a consistent style.

---

## Discord Commands & Administration

### Slash Commands

- **`/debug`**  
  *Description:* Toggle verbose logging and/or show the conversation context.  
  *Options:*
  - **action:** Choose among `'toggle'` (to switch verbose logging on/off), `'show'` (to display the conversation context via DM), or `'both'`.

- **`/reroll`**  
  *Description:* Reroll the last assistant response with optional additional context.  
  *Options:*
  - **context (optional):** Provide extra context that the bot should consider when generating a new response.

### Log Channel Text Commands

- **`shutdown? {DEFAULT_NAME}`**  
  *Description:* When an admin types `shutdown? CONFIRM`, the bot will announce its shutdown in the log channel and then disconnect. This update ensures a confirmation step is required to prevent accidental shutdowns.

- **`user data? [user_id]`**  
  *Description:* Retrieve detailed conversation data for a specified user (intended for troubleshooting memory saving/retrieval). Replace `[user_id]` with the actual user ID. If no data is found, the bot will indicate so.

> **Note:** These text-based commands are intended for administrative purposes and are processed only in the log channel.

---

## Setup and Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/character-driven-relationship-framework.git
   cd character-driven-relationship-framework
   ```

2. **Install Dependencies:**  
   Ensure you have Python 3.7+ installed and set up a virtual environment. Then install required packages:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: The repository requires packages such as `discord.py`, `aiofiles`, `python-dotenv`, among others.)*

3. **Configuration:**  
   Create a `.env` file in the project root with:
   ```dotenv
   ANTHROPIC_API_KEY="DUMMY_ANTHROPIC_API_KEY"
   discord_token="DUMMY_DISCORD_TOKEN"
   log_channel="DUMMY_LOG_CHANNEL"
   default_name="DUMMY_BOT_NAME"  # Optional: Overrides the default "Claude's Mask"
   core_prompt="CORE_PROMPT_PLACEHOLDER: Defines the bot's character and personality."
   summarization_prompt="SUMMARIZATION_PROMPT_PLACEHOLDER: Instructs the bot to summarize key points."
   core_memory_prompt="CORE_MEMORY_PROMPT_PLACEHOLDER: Directs memory updates."
   core_memory_dump="CORE_MEMORY_DUMP_PLACEHOLDER: Template for conversation history updates."
   ```

4. **Running the Bot:**  
   Start the bot by running:
   ```bash
   python main.py
   ```
   The bot will load user data, connect to Discord, and begin listening for messages based on the defined interaction principles and command structures.

---

## License

This project is licensed under the [MIT License](LICENSE).

