import abc
from typing import Callable

class BaseAgent(abc.ABC):
    """
    Abstract base class for all AI agents.
    Provides a common interface for agents that interact with an LLM.
    """
    def __init__(self, llm_caller: Callable[[str, float, int], str]):
        self.llm_caller = llm_caller

    @abc.abstractmethod
    def process(self, *args, **kwargs):
        """
        Abstract method to be implemented by concrete agents.
        Defines the core logic of the agent.
        """
        pass