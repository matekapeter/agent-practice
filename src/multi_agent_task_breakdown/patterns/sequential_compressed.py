"""
Pattern 4: Sequential with Compression (Scalable)
Graph Type: Sequential with compression nodes
Memory: Compressed context + vector retrieval
Coordination: Full coordination with memory management
Scalability: High - handles long tasks via compression
"""

from langgraph.graph import StateGraph, END

from ..agents.base_nodes import break_task_node
from ..agents.compression_nodes import (
    compress_context_node,
    compressed_agent_node,
    merge_compressed_node
)
from ..state import AgentState


def create_sequential_compressed_graph():
    """Create a sequential compressed graph with memory optimization."""
    
    workflow = StateGraph(AgentState)
    
    # Compression-aware nodes
    workflow.add_node("task_breaker", break_task_node)
    workflow.add_node("compress_1", compress_context_node)
    workflow.add_node("agent_1", lambda state: compressed_agent_node(state, "1"))
    workflow.add_node("compress_2", compress_context_node)
    workflow.add_node("agent_2", lambda state: compressed_agent_node(state, "2"))
    workflow.add_node("compress_final", compress_context_node)
    workflow.add_node("merger", merge_compressed_node)
    
    # Sequential with compression steps
    workflow.set_entry_point("task_breaker")
    workflow.add_edge("task_breaker", "compress_1")
    workflow.add_edge("compress_1", "agent_1")
    workflow.add_edge("agent_1", "compress_2")
    workflow.add_edge("compress_2", "agent_2")
    workflow.add_edge("agent_2", "compress_final")
    workflow.add_edge("compress_final", "merger")
    workflow.add_edge("merger", END)
    
    return workflow.compile()