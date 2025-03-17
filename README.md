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

   This dual approach captures both overarching themes and immediate details, with conversation summarization triggered when the conversation exceeds **25,000 tokens**.

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

## Bot Reply Logic

The bot follows distinct reply behaviors depending on whether it is interacting in a public channel or a private DM:

### **Direct Messages (DMs)**
- The bot **always** replies to messages in DMs.
- The conversation context remains private, allowing for a more casual, personal, and intimate interaction style.
- The system prompt includes a note emphasizing that the conversation is private and encourages natural interaction.

### **Public Channels**
- The bot will **only reply if explicitly mentioned by name** (`{DEFAULT_NAME}` in the message) or if it passes a voting system.
- If not mentioned, the bot determines whether to respond by running a yes/no voting process.
  - It gathers multiple AI-generated votes (**3 votes**) to decide whether to respond.
  - If the majority vote is **yes**, the bot replies.
- The bot limits responses to messages from other bots to avoid infinite loops.
- The system prompt reminds the bot that the conversation is public, encouraging it to maintain appropriate awareness.
- The bot incorporates up to **10 most recent messages** from the channel as external context when crafting a response.

---

## Available Commands

### **Slash Commands**

- **`/debug`**  
  *Description:* Toggle verbose logging and/or show the conversation context.  
  *Options:*
  - **action:** Choose among `'toggle'` (to switch verbose logging on/off), `'show'` (to display the conversation context via DM), or `'both'`.

- **`/reroll`**  
  *Description:* Reroll the last assistant response with optional additional context.  
  *Options:*
  - **context (optional):** Provide extra context that the bot should consider when generating a new response.

### **Log Channel Text Commands**

- **`shutdown? {DEFAULT_NAME}`**  
  *Description:* When an admin types `shutdown? {DEFAULT_NAME}`, the bot will announce its shutdown in the log channel and then disconnect.

- **`user data? [user_id]`**  
  *Description:* Retrieve detailed conversation data for a specified user (intended for troubleshooting memory saving/retrieval). Replace `[user_id]` with the actual user ID. If no data is found, the bot will indicate so.

> **Note:** These text-based commands are intended for administrative purposes and are processed only in the log channel.

---

## Project Structure

- **`memory.py`**  
  Contains logic for summarizing and archiving conversation history. When the estimated token count of a conversation becomes too high (above **25,000 tokens**), it automatically calls a summarizer to update core memories and condenses older conversation history into a brief summary.

- **`commands.py`**  
  Implements Discord slash commands (e.g., `/debug`, `/reroll`) and manages interactive elements like reroll views to refine assistant responses. The commands now incorporate improved handling of interactive message updates.

- **`utils.py`**  
  Provides helper functions for logging, message splitting, and sending messages that exceed Discord’s character limit.

- **`token_utils.py`**  
  Offers utility functions to estimate token counts and interface with Anthropic’s token counting API.

- **`config.py`**  
  Loads configuration from a `.env` file and sets up API keys, model names, and other environment-specific parameters.

- **`main.py`**  
  The entry point for the bot. It handles Discord event processing, manages conversation flow (including dynamic summarization of long conversations), and periodically saves user data. When coming online, the bot announces its presence by referencing the updated default name and dynamically adjusts response behavior based on context.

- **`ai.py`**  
  Handles API calls to Anthropic’s Claude, including token cost calculations, response logging, and error handling. It updates token usage for users and formats responses in a consistent style.

---

## Setup and Installation

### **Clone the Repository:**
```bash
git clone https://github.com/lastnpcalex/ClaudeMask.git
cd ClaudeMask
```

### **Install Dependencies:**  
Ensure you have Python 3.7+ installed and set up a virtual environment. Then install required packages:
```bash
pip install -r requirements.txt
```
*(Note: The repository requires packages such as `discord.py`, `aiofiles`, `python-dotenv`, among others.)*

### **Configuration:**  
Create a `.env` file in the project root with:
```dotenv
ANTHROPIC_API_KEY="DUMMY_ANTHROPIC_API_KEY"
discord_token="DUMMY_DISCORD_TOKEN"
log_channel="DUMMY_LOG_CHANNEL"
default_name="DUMMY_BOT_NAME"
core_prompt="CORE_PROMPT_PLACEHOLDER"
summarization_prompt="SUMMARIZATION_PROMPT_PLACEHOLDER"
core_memory_prompt="CORE_MEMORY_PROMPT_PLACEHOLDER"
core_memory_dump="CORE_MEMORY_DUMP_PLACEHOLDER"
```

### **Running the Bot:**  
Start the bot by running:
```bash
python main.py
```

---

## License

This project is licensed under the [MIT License](LICENSE).

