# token_utils.py
import anthropic
from config import OAI_TOKEN
from utils import log_error

def anthropic_token_count(model: str, system: str, messages: list):
    """
    Uses client.beta.messages.count_tokens to get the token count.
    According to the docs, the returned object has an 'input_tokens' attribute.
    If an error occurs, returns 0.
    """
    if not messages:
        messages = []
    try:
        client = anthropic.Anthropic(api_key=OAI_TOKEN)
        result = client.beta.messages.count_tokens(
            model=model,
            system=system,
            messages=messages
        )
        return result.input_tokens
    except Exception as e:
        log_error(f"Error using Anthropic messages.count_tokens: {e}. Falling back to 0.")
        return 0
