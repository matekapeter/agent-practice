"""
Multi-Agent Task Breakdown with LangChain/LangGraph and AWS Bedrock.

A comprehensive system for breaking down complex tasks into subtasks
and executing them using different coordination patterns.
"""

from .config import Config, config
from .orchestrator import MultiAgentOrchestrator, PatternType
from .state import AgentState

__version__ = "0.1.0"
__all__ = [
    "Config",
    "config", 
    "MultiAgentOrchestrator",
    "PatternType",
    "AgentState",
]