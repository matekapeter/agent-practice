"""
Pattern 1: Parallel Agents (Unreliable)
Demonstrates parallel execution with isolated agents and no coordination.

PROBLEMS THIS PATTERN SHOWS:
- Race conditions between agents
- No shared context or coordination
- Inconsistent results due to isolation
- Agents can't build on each other's work

This example is intentionally problematic to show why this pattern is unreliable.
"""

import os
from dotenv import load_dotenv
from langchain_aws import BedrockLLM
from langchain_community.embeddings import BedrockEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
import time
import threading

# Load environment variables
load_dotenv()

# AWS Bedrock setup
llm = BedrockLLM(
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

def break_task_node(state: AgentState) -> AgentState:
    """Break down a complex task into subtasks."""
    
    break_prompt = PromptTemplate(
        template="""
        You are a task breakdown specialist. Break the following complex task into 2-3 clear, actionable subtasks.
        
        Task: {task}
        
        Instructions:
        1. Analyze the task and identify logical components
        2. Create 2-3 subtasks that can be worked on independently
        3. Each subtask should be specific and actionable
        4. Return only the subtasks as a numbered list
        
        Subtasks:
        """,
        input_variables=["task"]
    )
    
    break_chain = LLMChain(llm=llm, prompt=break_prompt)
    result = break_chain.run(task=state["task"])
    
    # Parse the result into a list of subtasks
    subtasks = []
    for line in result.strip().split('\n'):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
            clean_task = line.lstrip('0123456789.-* ').strip()
            if clean_task:
                subtasks.append(clean_task)
    
    # Ensure we have at least 2 subtasks
    if len(subtasks) < 2:
        subtasks = [
            f"Research and analyze {state['task']}",
            f"Create detailed implementation plan for {state['task']}"
        ]
    
    state["subtasks"] = subtasks[:3]  # Limit to 3 subtasks
    state["step"] = "task_broken"
    
    return state

def sub_agent_node(state: AgentState, agent_id: str) -> AgentState:
    """Execute a subtask with an isolated agent - NO shared memory!"""
    
    # PROBLEM: Each agent gets isolated memory - no coordination
    isolated_memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    agent_prompt = PromptTemplate(
        template="""
        You are Sub-agent {agent_id}. You are working on a specific subtask as part of a larger project.
        
        Your task: {task}
        
        PROBLEM: You have NO context from other agents. You work in complete isolation.
        This means you might:
        - Duplicate work done by other agents
        - Miss important context from other parts of the project
        - Create inconsistent results
        
        Instructions:
        1. Focus only on your assigned subtask
        2. Provide detailed, actionable results
        3. Be thorough but concise
        4. Consider how your work might integrate with other subtasks (but you can't see their work!)
        
        Your response:
        """,
        input_variables=["agent_id", "task"]
    )
    
    chain = LLMChain(llm=llm, memory=isolated_memory, prompt=agent_prompt)
    
    task_index = int(agent_id) - 1
    if task_index < len(state["subtasks"]):
        result = chain.run(
            agent_id=agent_id,
            task=state["subtasks"][task_index]
        )
        state["sub_results"][agent_id] = result
        state["step"] = f"agent_{agent_id}_completed"
    
    return state

def merge_results_node(state: AgentState) -> AgentState:
    """Merge results from all agents into a final result."""
    
    merge_prompt = PromptTemplate(
        template="""
        You are a result merger. Combine the following subtask results into a comprehensive final result.
        
        PROBLEM: These results were created by isolated agents with no coordination.
        You may find:
        - Duplicate information
        - Contradictory approaches
        - Missing connections between subtasks
        - Inconsistent terminology or style
        
        Original task: {task}
        Subtask results:
        {results}
        
        Instructions:
        1. Synthesize all subtask results into a coherent final result
        2. Resolve any contradictions or duplications
        3. Ensure the final result addresses the original task completely
        4. Create a well-structured, professional output
        
        Final result:
        """,
        input_variables=["task", "results"]
    )
    
    merge_chain = LLMChain(llm=llm, prompt=merge_prompt)
    
    # Format results for the prompt
    results_text = ""
    for agent_id, result in state["sub_results"].items():
        results_text += f"\nAgent {agent_id}:\n{result}\n"
    
    final_result = merge_chain.run(
        task=state["task"],
        results=results_text
    )
    
    state["final_result"] = final_result
    state["step"] = "results_merged"
    
    return state

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

def main():
    """Demonstrate Pattern 1: Parallel Unreliable."""
    
    print("=== PATTERN 1: PARALLEL AGENTS (UNRELIABLE) ===\n")
    print("This pattern demonstrates the problems with isolated parallel agents:")
    print("❌ No shared context or coordination")
    print("❌ Race conditions possible")
    print("❌ Agents can't build on each other's work")
    print("❌ Inconsistent results due to isolation")
    print("❌ Duplicate work and contradictions\n")
    
    # Example task
    task = "Create a comprehensive marketing strategy for a new mobile app"
    print(f"Task: {task}\n")
    
    try:
        # Create and execute graph
        graph = create_parallel_unreliable_graph()
        
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
        
        print("Executing parallel unreliable pattern...")
        result = graph.invoke(initial_state)
        
        # Display results
        print(f"\nSubtasks created: {len(result['subtasks'])}")
        for i, subtask in enumerate(result['subtasks'], 1):
            print(f"  {i}. {subtask}")
        
        print(f"\nFinal Result Preview:")
        preview = result['final_result'][:300] + "..." if len(result['final_result']) > 300 else result['final_result']
        print(preview)
        
        print(f"\n=== PATTERN 1 ANALYSIS ===")
        print("Problems observed:")
        print("- Agents worked in complete isolation")
        print("- No shared memory or context")
        print("- Potential for duplicate work")
        print("- Merger had to resolve inconsistencies")
        print("- No coordination between agents")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()