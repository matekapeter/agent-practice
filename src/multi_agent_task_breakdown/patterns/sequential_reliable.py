"""
Pattern 3: Sequential Agents (Simple & Reliable)
Graph Type: Linear sequential execution
Memory: Cumulative context building
Coordination: Full - each agent builds on previous work
Reliability: High - deterministic execution order
"""

from langgraph.graph import StateGraph, END

from ..agents.base_nodes import break_task_node, sequential_agent_node, merge_sequential_node
from ..state import AgentState


def create_sequential_reliable_graph():
    """Create a sequential reliable graph with cumulative context."""
    
    workflow = StateGraph(AgentState)
    
    # Sequential nodes
    workflow.add_node("task_breaker", break_task_node)
    workflow.add_node("agent_1", lambda state: sequential_agent_node(state, "1"))
    workflow.add_node("agent_2", lambda state: sequential_agent_node(state, "2"))
    workflow.add_node("merger", merge_sequential_node)
    
    # Linear execution path
    workflow.set_entry_point("task_breaker")
    workflow.add_edge("task_breaker", "agent_1")
    workflow.add_edge("agent_1", "agent_2")
    workflow.add_edge("agent_2", "merger")
    workflow.add_edge("merger", END)
    
    return workflow.compile()