"""
Main orchestrator for the multi-agent task breakdown system.
Provides a unified interface for executing tasks with different patterns.
"""

from typing import Literal, Optional

from .patterns import (
    create_parallel_unreliable_graph,
    create_parallel_shared_graph,
    create_sequential_reliable_graph,
    create_sequential_compressed_graph,
)
from .state import AgentState

PatternType = Literal["parallel_unreliable", "parallel_shared", "sequential_reliable", "sequential_compressed"]


class MultiAgentOrchestrator:
    """Main orchestrator for multi-agent task breakdown."""
    
    def __init__(self, pattern: PatternType = "sequential_reliable"):
        """
        Initialize the orchestrator with a specific pattern.
        
        Args:
            pattern: The pattern to use for task execution
        """
        self.pattern = pattern
        self.graph = self._create_graph(pattern)
    
    def _create_graph(self, pattern: PatternType):
        """Create the appropriate graph based on the pattern."""
        pattern_map = {
            "parallel_unreliable": create_parallel_unreliable_graph,
            "parallel_shared": create_parallel_shared_graph,
            "sequential_reliable": create_sequential_reliable_graph,
            "sequential_compressed": create_sequential_compressed_graph,
        }
        
        if pattern not in pattern_map:
            raise ValueError(f"Unknown pattern: {pattern}")
        
        return pattern_map[pattern]()
    
    def execute_task(
        self,
        task: str,
        pattern: Optional[PatternType] = None
    ) -> AgentState:
        """
        Execute a task using the specified pattern.
        
        Args:
            task: The task to execute
            pattern: Optional pattern override
            
        Returns:
            The final state with results
        """
        if pattern and pattern != self.pattern:
            self.pattern = pattern
            self.graph = self._create_graph(pattern)
        
        # Initialize state
        initial_state = AgentState(
            messages=[],
            task=task,
            subtasks=[],
            sub_results={},
            final_result="",
            context="",
            compressed_context="",
            step="start"
        )
        
        # Execute the graph
        result = self.graph.invoke(initial_state)
        return result
    
    def get_pattern_info(self) -> dict:
        """Get information about the current pattern."""
        pattern_info = {
            "parallel_unreliable": {
                "name": "Parallel Agents (Unreliable)",
                "description": "Parallel execution with isolated agents",
                "memory": "Isolated per agent",
                "coordination": "None",
                "reliability": "Low - race conditions possible"
            },
            "parallel_shared": {
                "name": "Parallel with Shared Context",
                "description": "Parallel execution with shared memory",
                "memory": "Shared conversation buffer",
                "coordination": "Minimal",
                "reliability": "Low - timing issues possible"
            },
            "sequential_reliable": {
                "name": "Sequential Agents (Reliable)",
                "description": "Linear sequential execution",
                "memory": "Cumulative context building",
                "coordination": "Full",
                "reliability": "High - deterministic"
            },
            "sequential_compressed": {
                "name": "Sequential with Compression",
                "description": "Sequential with memory optimization",
                "memory": "Compressed context + vector retrieval",
                "coordination": "Full with memory management",
                "reliability": "High - scalable"
            }
        }
        
        return pattern_info.get(self.pattern, {})