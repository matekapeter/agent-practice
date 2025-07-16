"""
State schema for the multi-agent task breakdown system.
Defines the AgentState TypedDict and related types.
"""

import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict):
    """State schema for the multi-agent system."""
    
    # Core task information
    messages: Annotated[list, operator.add]  # Accumulated messages
    task: str  # Original task description
    subtasks: list[str]  # List of broken down subtasks
    sub_results: dict[str, str]  # Results from each subtask agent
    
    # Results and context
    final_result: str  # Final merged result
    context: str  # Current working context
    compressed_context: str  # Compressed version of context
    
    # Workflow control
    step: str  # Current step in the workflow