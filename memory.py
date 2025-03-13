# memory.py
import json
import pickle
from ai import anthropic_token_count

class MemoryManager:
    """
    Manages per-user memory for short-term conversation events.
    Keeps a summary (under a target token limit) that aggregates repeated events.
    Non-pivotal events (those that occur rarely) may be dumped to deep memory.
    """
    def __init__(self, summary_limit=2000, deep_memory_file="deep_memory.json"):
        self.summary_limit = summary_limit  # maximum tokens in summary
        self.memory = {}  # {user_id: {"events": {event: count}, "summary": str}}
        self.deep_memory_file = deep_memory_file
        try:
            with open(deep_memory_file, "r") as f:
                self.deep_memory = json.load(f)
        except Exception:
            self.deep_memory = {}

    def add_event(self, user_id: str, event_text: str):
        """
        Add an event for the given user. If the event already exists exactly, increment its count.
        """
        if user_id not in self.memory:
            self.memory[user_id] = {"events": {}}
        events = self.memory[user_id]["events"]
        if event_text in events:
            events[event_text] += 1
        else:
            events[event_text] = 1

    def generate_summary(self, user_id: str) -> str:
        """
        Generate a summary string from the user's events.
        Pivotal events (with count >= 3) are always kept.
        Non-pivotal events are added only if they do not exceed the summary token limit.
        """
        if user_id not in self.memory:
            return ""
        events = self.memory[user_id]["events"]
        summary_lines = []
        non_pivotal = {}
        for event, count in events.items():
            if count >= 3:
                summary_lines.append(f"{event} (x{count})")
            else:
                non_pivotal[event] = count
        summary = "\n".join(summary_lines)
        # Try adding non-pivotal events if room allows
        for event, count in non_pivotal.items():
            line = f"{event} (x{count})" if count > 1 else event
            if anthropic_token_count(summary + "\n" + line) < self.summary_limit:
                summary += "\n" + line
            else:
                self.dump_to_deep_memory(user_id, event, count)
        self.memory[user_id]["summary"] = summary
        return summary

    def dump_to_deep_memory(self, user_id: str, event: str, count: int):
        """
        Dump a non-pivotal event into deep memory and remove it from short-term memory.
        """
        if user_id not in self.deep_memory:
            self.deep_memory[user_id] = {}
        self.deep_memory[user_id][event] = count
        if user_id in self.memory and event in self.memory[user_id]["events"]:
            del self.memory[user_id]["events"][event]
        with open(self.deep_memory_file, "w") as f:
            json.dump(self.deep_memory, f, indent=2)

    def reset_memory(self, user_id: str):
        """
        Reset the short-term memory for a given user.
        """
        if user_id in self.memory:
            self.memory[user_id]["events"] = {}
            self.memory[user_id]["summary"] = ""

    def get_full_memory(self, user_id: str) -> (str, dict):
        """
        Return the current summary and deep memory for the user.
        """
        summary = self.generate_summary(user_id)
        deep = self.deep_memory.get(user_id, {})
        return summary, deep

# Create a global MemoryManager instance
memory_manager = MemoryManager()
