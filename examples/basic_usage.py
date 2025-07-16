"""
Basic usage example for the Multi-Agent Task Breakdown system.
Demonstrates how to use different patterns for task execution.

This example shows the basic patterns without advanced memory management.
For production use, see the enhanced examples with episodic/semantic memory.
"""

import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# Load environment variables
load_dotenv()

# AWS Bedrock setup
llm = ChatBedrock(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    region_name="us-east-1",
    max_tokens=4096,
    temperature=0.1,
    model_kwargs={"anthropic_version": "bedrock-2023-05-31"}
)

embeddings = BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v1",
    region_name="us-east-1"
)

# Memory systems
short_term_memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

vector_store = FAISS.from_texts([""], embeddings)
long_term_memory = ConversationBufferMemory(
    memory_key="relevant_context",
    return_messages=True
)

# State schema
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    task: str
    subtasks: list[str]
    sub_results: dict[str, str]
    final_result: str
    context: str
    compressed_context: str
    step: str

# Pattern implementations
def break_task_node(state: AgentState) -> AgentState:
    """Break down a complex task into subtasks."""
    break_prompt = PromptTemplate(
        template="""
        You are a task breakdown specialist.
        
        TASK: {task}
        
        Instructions:
        1. Analyze the task and identify logical components
        2. Create 2-3 subtasks that can be worked on sequentially
        3. Each subtask should build upon the previous one
        4. Return only the subtasks as a numbered list
        
        Subtasks:
        """,
        input_variables=["task"]
    )
    
    break_chain = LLMChain(llm=llm, prompt=break_prompt)
    result = break_chain.run(task=state["task"])
    
    # Parse subtasks from result
    subtasks = []
    for line in result.strip().split('\n'):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
            # Remove numbering/bullets and clean up
            clean_line = line.lstrip('0123456789.-* ').strip()
            if clean_line:
                subtasks.append(clean_line)
    
    state["subtasks"] = subtasks[:3]  # Limit to 3 subtasks
    state["step"] = "task_broken_down"
    
    return state

def basic_agent_node(state: AgentState, agent_id: str) -> AgentState:
    """Basic agent node for sequential execution."""
    agent_prompt = PromptTemplate(
        template="""
        You are Sub-agent {agent_id}.
        
        Previous context: {context}
        Current task: {task}
        
        Complete your task and provide a detailed response.
        """,
        input_variables=["agent_id", "context", "task"]
    )
    
    agent_chain = LLMChain(llm=llm, prompt=agent_prompt)
    result = agent_chain.run(
        agent_id=agent_id,
        context=state.get("context", ""),
        task=state["subtasks"][int(agent_id)-1]
    )
    
    state["sub_results"][agent_id] = result
    state["context"] += f"\n[Agent {agent_id}]: {result}"
    state["step"] = f"agent_{agent_id}_completed"
    
    return state

def merge_results_node(state: AgentState) -> AgentState:
    """Merge results from all agents."""
    merge_prompt = PromptTemplate(
        template="""
        You are a result synthesis specialist.
        
        Original task: {task}
        
        Results from agents:
        {results}
        
        Synthesize these results into a comprehensive final answer.
        Ensure the final result addresses all aspects of the original task.
        """,
        input_variables=["task", "results"]
    )
    
    results_text = "\n\n".join([
        f"Agent {k}: {v}" for k, v in state["sub_results"].items()
    ])
    
    merge_chain = LLMChain(llm=llm, prompt=merge_prompt)
    final_result = merge_chain.run(
        task=state["task"],
        results=results_text
    )
    
    state["final_result"] = final_result
    state["step"] = "completed"
    
    return state

def create_sequential_reliable_graph():
    """Create a sequential reliable graph."""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("task_breaker", break_task_node)
    workflow.add_node("agent_1", lambda state: basic_agent_node(state, "1"))
    workflow.add_node("agent_2", lambda state: basic_agent_node(state, "2"))
    workflow.add_node("merger", merge_results_node)
    
    workflow.set_entry_point("task_breaker")
    workflow.add_edge("task_breaker", "agent_1")
    workflow.add_edge("agent_1", "agent_2")
    workflow.add_edge("agent_2", "merger")
    workflow.add_edge("merger", END)
    
    return workflow.compile()

def create_parallel_unreliable_graph():
    """Create a parallel unreliable graph."""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("task_breaker", break_task_node)
    workflow.add_node("agent_1", lambda state: basic_agent_node(state, "1"))
    workflow.add_node("agent_2", lambda state: basic_agent_node(state, "2"))
    workflow.add_node("merger", merge_results_node)
    
    workflow.set_entry_point("task_breaker")
    workflow.add_edge("task_breaker", "agent_1")
    workflow.add_edge("task_breaker", "agent_2")
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

def execute_pattern(pattern: str, task: str) -> AgentState:
    """Execute a task using the specified pattern."""
    
    # Create graph based on pattern
    if pattern == "sequential_reliable":
        graph = create_sequential_reliable_graph()
    elif pattern == "parallel_unreliable":
        graph = create_parallel_unreliable_graph()
    else:
        raise ValueError(f"Unknown pattern: {pattern}")
    
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
    result = graph.invoke(initial_state)
    return result

def get_pattern_info(pattern: str) -> dict:
    """Get information about a pattern."""
    pattern_info = {
        "parallel_unreliable": {
            "name": "Parallel Agents (Unreliable)",
            "description": "Parallel execution with isolated agents",
            "memory": "Isolated per agent",
            "coordination": "None",
            "reliability": "Low - race conditions possible"
        },
        "sequential_reliable": {
            "name": "Sequential Agents (Reliable)",
            "description": "Linear sequential execution",
            "memory": "Cumulative context building",
            "coordination": "Full",
            "reliability": "High - deterministic"
        }
    }
    
    return pattern_info.get(pattern, {})

def main():
    """Main example function."""
    
    # Example task
    task = "Create a comprehensive marketing strategy for a new mobile app"
    
    print("=== Multi-Agent Task Breakdown Example ===\n")
    print(f"Task: {task}\n")
    
    # Test different patterns
    patterns = ["sequential_reliable", "parallel_unreliable"]
    
    for pattern in patterns:
        print(f"--- Testing Pattern: {pattern} ---")
        
        try:
            # Get pattern info
            info = get_pattern_info(pattern)
            print(f"Pattern: {info.get('name', pattern)}")
            print(f"Description: {info.get('description', 'N/A')}")
            print(f"Memory: {info.get('memory', 'N/A')}")
            print(f"Reliability: {info.get('reliability', 'N/A')}")
            
            # Execute task
            print("\nExecuting task...")
            result = execute_pattern(pattern, task)
            
            # Display results
            print(f"\nSubtasks created: {len(result['subtasks'])}")
            for i, subtask in enumerate(result['subtasks'], 1):
                print(f"  {i}. {subtask}")
            
            print(f"\nFinal Result Preview:")
            preview = result['final_result'][:200] + "..." if len(result['final_result']) > 200 else result['final_result']
            print(preview)
            
        except Exception as e:
            print(f"Error with pattern {pattern}: {e}")
        
        print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    main()