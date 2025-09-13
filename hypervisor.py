from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from ai import call_claude
from config import DEFAULT_MODEL
from utils import log_error


@dataclass
class Character:
    """Represents an individual roleplay character."""
    name: str
    prompt: str
    state: Dict[str, Any] = field(default_factory=dict)


class Hypervisor:
    """Orchestrates multi-character roleplay interactions.

    The Hypervisor receives human messages, determines which characters are
    involved, routes the prompts to the appropriate character LLMs, and
    validates that responses stay in character.
    """

    def __init__(self, characters: Dict[str, Character]):
        # Normalize keys to lowercase for matching
        self.characters: Dict[str, Character] = {
            c.name.lower(): c for c in characters.values()
        }
        # Separate user dict for each character for conversation history
        self.user_dict: Dict[str, Dict[str, Any]] = {}

    # -----------------------------------------------------
    # Message analysis
    # -----------------------------------------------------
    def detect_characters(self, message: str) -> List[Character]:
        """Return a list of characters explicitly mentioned in the message."""
        msg_lower = message.lower()
        detected = []
        for key, character in self.characters.items():
            if re.search(rf"\b{re.escape(key)}\b", msg_lower):
                detected.append(character)
        return detected

    def determine_turn_order(self, message: str, characters: List[Character]) -> List[Character]:
        """Order characters based on their first appearance in the message."""
        msg_lower = message.lower()
        return sorted(
            characters,
            key=lambda c: msg_lower.find(c.name.lower())
        )

    # -----------------------------------------------------
    # LLM interaction
    # -----------------------------------------------------
    async def _query_character(self, character: Character, message: str, history: List[Dict[str, str]]) -> str:
        """Send the message to the character's LLM and return the response text."""
        system_prompt = character.prompt
        try:
            result = await call_claude(
                user_id=character.name,
                user_dict=self.user_dict,
                model=DEFAULT_MODEL,
                system_prompt=system_prompt,
                user_content=message,
                temperature=1.0,
                max_tokens=500,
                verbose=False,
            )
            return result.choices[0].message["content"].strip()
        except Exception as e:
            log_error(f"Hypervisor failed to query {character.name}: {e}")
            return ""

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------
    def validate_response(self, character: Character, response: str) -> bool:
        """Basic in-character validation checks."""
        if not response:
            return False
        # Meta-awareness checks
        meta_patterns = [
            r"as a large language model",
            r"as an ai assistant",
            r"i am an ai",
        ]
        for pat in meta_patterns:
            if re.search(pat, response, re.IGNORECASE):
                return False
        # Name consistency
        if re.search(r"my name is (?!" + re.escape(character.name) + r")", response, re.IGNORECASE):
            return False
        return True

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------
    async def route_message(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Process a human message and return hypervisor output.

        Returns a dict with keys:
            - decision_log: explanation of routing
            - responses: list of {name: str, content: str}
            - state_update: updated character states
            - next_expected: which character might respond next (if any)
        """
        history = history or []

        detected = self.detect_characters(message)
        if not detected:
            return {
                "decision_log": "No known characters referenced.",
                "responses": [],
                "state_update": {},
                "next_expected": None,
            }

        ordered = self.determine_turn_order(message, detected)
        responses = []
        decision_steps = [
            f"Detected characters: {', '.join([c.name for c in ordered])}"
        ]

        for char in ordered:
            text = await self._query_character(char, message, history)
            if not self.validate_response(char, text):
                decision_steps.append(
                    f"{char.name} response failed validation; using fallback."
                )
                text = "(The character seems unable to respond in character.)"
            responses.append({"name": char.name, "content": text})
            history.append({"role": char.name, "content": text})

        next_expected = ordered[-1].name if ordered else None
        return {
            "decision_log": " | ".join(decision_steps),
            "responses": responses,
            "state_update": {c.name: c.state for c in ordered},
            "next_expected": next_expected,
        }


__all__ = ["Character", "Hypervisor"]
