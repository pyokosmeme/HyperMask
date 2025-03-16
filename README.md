# Character-Driven Relationship Framework

This repository contains a comprehensive framework for creating engaging LLM-based personas using Anthropic’s Claude. Designed to be both flexible and robust, this system enables you to explore a wide range of relationship dynamics—from mentorships and familial bonds to professional collaborations and beyond. While our initial example focuses on intimate and mentorship relationships, the template is fully adaptable for virtually any interpersonal dynamic.

---

## Overview

The framework is built around four key components:

1. **Character Definition Template**  
   Create richly detailed personas with distinctive traits, communication styles, and a dual-mode system. For example, the character *Theia* can switch between a “cosmic shield” mode and direct communication, allowing nuanced expression based on context.

2. **Interaction Principles**  
   Establish and evolve relationship dynamics by following clear guidelines—from the initial encounter to deep, multifaceted connections. The system breaks down relationship progression into distinct stages, ensuring natural development and engagement.

3. **Memory Archiving System**  
   Record relationship developments using two formats:
   - A **comprehensive record** that tracks long-term evolution.
   - A **quick update format** for real-time insights and recent interactions.

   This dual approach ensures that both overarching themes and immediate changes are captured and can inform future interactions.

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

## Implementation Example

As a demonstration, the repository includes an implementation that sets up a mentorship relationship between *Maya* (a forest ranger with deep ecological insight) and *Eli* (a city-dwelling graduate student). In this example:
- **Character Definition:** Maya uses nature metaphors and shifts her tone from reserved to passionate when discussing conservation.
- **Interaction Principles:** The dynamic evolves from a knowledge imbalance (teacher/student) to a mutually respectful collaboration.
- **Memory Archiving:** Both long-term growth and short-term updates are captured, ensuring that each milestone is noted and leveraged in subsequent interactions.

---

## Project Structure

- **`memory.py`**  
  Contains logic for summarizing and archiving conversation history. It uses a pickled log to persist core memories when the conversation exceeds a set token limit.

- **`commands.py`**  
  Implements Discord slash commands (e.g., `/debug`, `/reroll`) and manages interactive elements like reroll views to refine assistant responses.

- **`utils.py`**  
  Provides helper functions for logging, message splitting, and sending messages that exceed Discord’s character limit.

- **`token_utils.py`**  
  Offers utility functions to estimate token counts and interface with Anthropic’s token counting API.

- **`config.py`**  
  Loads configuration from a dummy `.env` file and sets up model names, API keys, and other environment-specific parameters.

- **`main.py`**  
  The entry point for the bot. It manages Discord event handling, conversation flow, periodic data saving, and integrates the various components of the framework.

- **`ai.py`**  
  Handles API calls to Anthropic’s Claude, including token cost calculations and response logging.

---

## Discord Commands & Administration

This framework integrates with Discord through both slash commands and admin text commands. Here's a quick guide to the available commands:

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

In addition to the slash commands, the bot listens for specific commands in the designated log channel:

- **`shutdown?`**  
  *Description:* When an admin types `shutdown?`, the bot will announce its shutdown in the log channel and then disconnect.

- **`user data? [user_id]`**  
  *Description:* Retrieve detailed conversation data for a specified user (intended use is troubleshooting memory saving/retrieval). Replace `[user_id]` with the actual user ID. If no data is found, the bot will inform you accordingly.

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
   *(Note: Make sure to include packages such as `discord.py`, `aiofiles`, `python-dotenv`, and any other dependencies based on your project needs.)*

3. **Configuration:**  
   Create a `.env` file in the project root. You can start with the following dummy configuration (update with your actual keys):
   ```dotenv
   ANTHROPIC_API_KEY="DUMMY_ANTHROPIC_API_KEY"
   discord_token="DUMMY_DISCORD_TOKEN"
   bot_usr_id="DUMMY_BOT_USER_ID"
   default_name="DUMMY_BOT_NAME"
   description="DUMMY_DESCRIPTION: Placeholder description of the bot's persona."
   log_channel="DUMMY_LOG_CHANNEL"

   core_prompt="CORE_PROMPT_PLACEHOLDER: [Explanation: Defines the bot's character, personality, and roleplaying guidelines with example responses.]"
   summarization_prompt="SUMMARIZATION_PROMPT_PLACEHOLDER: [Explanation: Instructs the bot to summarize conversation details focusing on key points and context.]"
   core_memory_prompt="CORE_MEMORY_PROMPT_PLACEHOLDER: [Explanation: Directs the bot to update its internal memory with recent conversation details and observations.]"
   core_memory_dump="CORE_MEMORY_DUMP_PLACEHOLDER: [Explanation: Template for generating a comprehensive update of the bot's conversation history and key milestones.]"
   ```

4. **Running the Bot:**  
   Start the bot by running:
   ```bash
   python main.py
   ```
   The bot will load user data, connect to Discord, and begin listening for messages based on the defined interaction principles and command structures.

---

## Customization

This framework is designed to be highly adaptable:
- **Character Prompts:** Use the provided template to create distinct personas. Experiment with unique communication styles and relationship approaches.
- **Interaction Rules:** Adjust the interaction stages to suit the relationship type you want to explore.
- **Memory Management:** Modify the archiving formats to capture additional details or streamline conversation summaries.
- **Relationship Types:** Leverage the Customization Guide to tailor the framework for romantic, familial, mentorship, adversarial, platonic, or professional dynamics.

---

## License

This project is licensed under the [MIT License](LICENSE).
