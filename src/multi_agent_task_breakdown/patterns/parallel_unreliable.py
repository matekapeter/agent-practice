"""
Pattern 1: Parallel Agents (Unreliable)
Graph Type: Parallel execution with conditional edges
Memory: Isolated per agent (no shared context)
Coordination: None - agents work independently
Expected Issues: Race conditions, inconsistent results
"""

from langgraph.graph import StateGraph, END

from ..agents.base_nodes import break_task_node, sub_agent_node, merge_results_node
from ..state import AgentState


def create_parallel_unreliable_graph():
    """Create a parallel unreliable graph with isolated agents."""
    
    workflow = StateGraph(AgentState)
    
    # Nodes
    workflow.add_node("task_breaker", break_task_node)
    workflow.add_node("agent_1", lambda state: sub_agent_node(state, "1"))
    workflow.add_node("agent_2", lambda state: sub_agent_node(state, "2"))
    workflow.add_node("merger", merge_results_node)
    
    # Edges - parallel execution
    workflow.set_entry_point("task_breaker")
    workflow.add_edge("task_breaker", "agent_1")
    workflow.add_edge("task_breaker", "agent_2")
    
    # Conditional edges for synchronization
    workflow.add_conditional_edges(
        "agent_1",
        lambda state: "merge" if len(state["sub_results"]) == 2 else "wait",
        {"merge": "merger", "wait": END}
    )
    workflow.add_conditional_edges(
        "agent_2", 
        lambda state: "merge" if len(state["sub_results"]) == 2 else "wait",
        {"merge": "merger", "wait": END}
    )
    workflow.add_edge("merger", END)
    
    return workflow.compile()