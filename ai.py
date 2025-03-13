# ai.py
import asyncio
import aiohttp
import anthropic  # Ensure you have the Anthropic Python client installed
from config import OAI_TOKEN, DEFAULT_MODEL, PREMIUM_MODEL, COST_PER_TOKEN_HAIKU, COST_PER_TOKEN_SONNET, TOKEN_LIMIT, DEFAULT_NAME
from utils import log_error

# Set Anthropic API key if needed (depends on the client library's setup)
# e.g., anthropic.api_key = OAI_TOKEN

def anthropic_token_count(text: str) -> int:
    """
    Uses Anthropic's official tokenizer to count tokens.
    If unavailable, falls back to a simple whitespace split.
    """
    try:
        tokens = anthropic.tokenizer.encode(text)
        return len(tokens)
    except Exception as e:
        log_error(f"Anthropic tokenizer error: {e}. Falling back to whitespace split.")
        return len(text.split())

async def call_claude(user_id, user_dict, model, role, content, temperature, n, presence_penalty, max_tokens, temp_override: bool, verbose=False):
    """
    Calls Anthropic's Claude API using the proper endpoint and payload.
    
    The prompt is constructed in a Claude-friendly format:
      "<role prompt>\nSenpai: <content>\n<AssistantName>:"
    and uses stop sequence "\nSenpai:".
    """
    # Adjust temperature if needed.
    if temp_override:
        temperature = 1.05 if model == PREMIUM_MODEL else 1.15

    # Construct the prompt using the desired format.
    # 'role' contains our system prompt (personality details).
    prompt = f"{role}\nSenpai: {content}\n{DEFAULT_NAME}:"
    
    data = {
        "model": model,
        "prompt": prompt,
        "max_tokens_to_sample": max_tokens,
        "temperature": temperature,
        "stop_sequences": ["\nSenpai:"]
    }

    headers = {
        "x-api-key": OAI_TOKEN,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    url = "https://api.anthropic.com/v1/complete"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers, timeout=max_tokens/10) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    log_error(f"Anthropic API error {resp.status}: {error_text}")
                    raise Exception(f"Anthropic API error: {resp.status}")
                response_json = await resp.json()
    except asyncio.TimeoutError:
        fallback = "Please re-do that answer; be explicit and do not be vague."
        response_json = {"completion": fallback}
    except Exception as e:
        log_error(f"Error in call_claude: {e}")
        fallback = "An error occurred. Please try again later."
        response_json = {"completion": fallback}

    # Wrap the response in an object similar to the previous structure.
    class FakeChoice:
        def __init__(self, message):
            self.message = message
    class FakeResponse:
        def __init__(self, completion):
            self.choices = [FakeChoice({"content": completion})]
    fake_response = FakeResponse(response_json.get("completion", ""))

    # Count tokens using Anthropic's token counter.
    prompt_tokens = anthropic_token_count(prompt + role)
    completion_tokens = anthropic_token_count(response_json.get("completion", ""))
    total_tokens = prompt_tokens + completion_tokens

    # Calculate cost and update user token usage.
    if model == PREMIUM_MODEL:
        cost = total_tokens * COST_PER_TOKEN_SONNET
    else:
        cost = total_tokens * COST_PER_TOKEN_HAIKU
    user_dict.setdefault(user_id, {})["token_usage"] = user_dict.get(user_id, {}).get("token_usage", 0) + total_tokens

    if verbose:
        log_error(f"[Verbose] User {user_id} prompt:\n{prompt}\nResponse:\n{response_json.get('completion', '')}")

    return fake_response
