"""
Pattern 2: Parallel with Shared Context (Still Unreliable)
Graph Type: Parallel execution with shared memory
Memory: Shared conversation buffer with locks
Coordination: Minimal - agents see same conversation
Expected Issues: Timing issues, memory corruption
"""

from langchain.memory import ConversationBufferMemory
from langgraph.graph import StateGraph, END

from ..agents.base_nodes import break_task_node, shared_agent_node, merge_with_context_node
from ..state import AgentState


def create_parallel_shared_graph():
    """Create a parallel shared graph with shared memory."""
    
    workflow = StateGraph(AgentState)
    
    # Shared memory system
    shared_memory = ConversationBufferMemory(
        memory_key="shared_history",
        return_messages=True
    )
    
    # Nodes
    workflow.add_node("task_breaker", break_task_node)
    workflow.add_node("agent_1", lambda state: shared_agent_node(state, "1", shared_memory))
    workflow.add_node("agent_2", lambda state: shared_agent_node(state, "2", shared_memory))
    workflow.add_node("merger", merge_with_context_node)
    
    # Same parallel structure as Pattern 1
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