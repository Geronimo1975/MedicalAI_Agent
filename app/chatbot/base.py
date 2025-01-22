from abc import ABC, abstractmethod
from typing import List, Dict

class BaseChatModel(ABC):
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a response based on the conversation history."""
        pass

    @abstractmethod
    def generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """Generate a summary of the conversation."""
        pass

    @abstractmethod
    def determine_triage_level(self, messages: List[Dict[str, str]]) -> str:
        """Determine the urgency level of the medical situation."""
        pass
