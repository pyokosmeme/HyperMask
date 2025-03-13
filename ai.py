# ai.py
import asyncio
import openai
from config import OAI_TOKEN, DEFAULT_MODEL, PREMIUM_MODEL, COST_PER_TOKEN_HAIKU, COST_PER_TOKEN_SONNET, TOKEN_LIMIT
from utils import log_error
import time

# Set Anthropic API key (assumed here via openai module for simplicity)
openai.api_key = OAI_TOKEN

def anthropic_token_count(text: str) -> int:
    """
    A simple token counter for Anthropic's models.
    (This is a placeholder – replace with a proper implementation if available.)
    """
    return len(text.split())

async def call_claude(user_id, user_dict, model, role, content, temperature, n, presence_penalty, max_tokens, temp_override: bool, verbose=False):
    """
    Sends a prompt to Claude via the API.
    The model parameter should be either DEFAULT_MODEL or PREMIUM_MODEL.
    """
    # Set timeout and adjust temperature based on the model
    if model == DEFAULT_MODEL:
        timeout = 45
        if temp_override:
            temperature = 1.15
    elif model == PREMIUM_MODEL:
        timeout = 100
        if temp_override:
            temperature = 1.05
    else:
        timeout = 60

    messages = [
        {"role": "system", "content": role},
        {"role": "user", "content": content}
    ]
    try:
        response = await asyncio.wait_for(
            openai.ChatCompletion.acreate(
                model=model,
                messages=messages,
                temperature=temperature,
                n=n,
                presence_penalty=presence_penalty,
                max_tokens=max_tokens
            ),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        fallback = "Please re-do that answer; be explicit and do not be vague."
        response = type("FakeResponse", (), {})()
        response.choices = [{"message": {"content": fallback}} for _ in range(n)]
    except Exception as e:
        log_error(f"Error in call_claude: {e}")
        fallback = "An error occurred. Please try again later."
        response = type("FakeResponse", (), {})()
        response.choices = [{"message": {"content": fallback}} for _ in range(n)]

    # Token counting using our new counter
    prompt_tokens = anthropic_token_count(content + role)
    completion_str = ""
    for choice in response.choices:
        try:
            completion_str += choice["message"]["content"]
        except Exception as e:
            log_error(f"Error extracting message content: {e}")
    completion_tokens = anthropic_token_count(completion_str)

    # Calculate cost and update user_dict
    total_tokens = completion_tokens + prompt_tokens
    if model == PREMIUM_MODEL:
        cost = total_tokens * COST_PER_TOKEN_SONNET
    else:
        cost = total_tokens * COST_PER_TOKEN_HAIKU
    user_dict.setdefault(user_id, {})["token_usage"] = user_dict.get(user_id, {}).get("token_usage", 0) + total_tokens

    if verbose:
        log_error(f"[Verbose] User {user_id} prompt:\n{role}\n{content}\nResponse:\n{completion_str}")

    return response

async def get_embedding(text, model="text-embedding-ada-002"):
    """
    Retrieves an embedding for a given text.
    """
    clean_text = text.replace("\n", " ")
    try:
        embed = await openai.Embedding.acreate(input=[clean_text], model=model)
    except Exception as e:
        log_error(f"Error in get_embedding: {e}")
        embed = {"data": [{"embedding": []}]}
    return embed

# (Optionally, add a stub for multimodal image analysis if needed.)
async def analyze_image(image_url: str) -> str:
    """
    Stub: Analyze an image given its URL using Claude's multimodal capabilities.
    (You would need to implement the actual image handling and API call.)
    """
    return f"Analysis of image at {image_url}: [result]"
