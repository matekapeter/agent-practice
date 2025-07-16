"""
Pattern 2: Parallel with Shared Context (Still Unreliable)
Demonstrates parallel execution with shared memory but still has coordination issues.

PROBLEMS THIS PATTERN SHOWS:
- Timing issues with shared memory access
- Memory corruption from concurrent writes
- Agents can see each other's work but execution is still parallel
- Race conditions in memory updates
- Inconsistent state due to parallel execution

This example shows why shared memory doesn't solve parallel coordination problems.
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

def shared_agent_node(state: AgentState, agent_id: str, shared_memory) -> AgentState:
    """Execute a subtask with shared memory - but execution is still parallel!"""
    
    agent_prompt = PromptTemplate(
        template="""
        You are Sub-agent {agent_id}. You are working on a specific subtask as part of a larger project.
        
        Shared context: {history}
        Your task: {task}
        
        PROBLEM: You can see shared context, but execution is still parallel.
        This means:
        - You might read outdated information from other agents
        - Your updates might overwrite other agents' work
        - Race conditions in memory access
        - Inconsistent state due to timing issues
        
        Instructions:
        1. Consider the shared context from other agents
        2. Focus on your assigned subtask
        3. Provide detailed, actionable results
        4. Build upon or complement work from other agents
        5. Be aware that the shared context might change while you're working
        
        Your response:
        """,
        input_variables=["agent_id", "history", "task"]
    )
    
    chain = LLMChain(llm=llm, memory=shared_memory, prompt=agent_prompt)
    
    task_index = int(agent_id) - 1
    if task_index < len(state["subtasks"]):
        result = chain.run(
            agent_id=agent_id,
            history=state.get("context", ""),
            task=state["subtasks"][task_index]
        )
        state["sub_results"][agent_id] = result
        state["step"] = f"agent_{agent_id}_completed"
    
    return state

def merge_with_context_node(state: AgentState) -> AgentState:
    """Merge results with shared context consideration."""
    
    merge_prompt = PromptTemplate(
        template="""
        You are a result merger. Combine the following subtask results into a comprehensive final result.
        
        PROBLEM: These results were created by agents with shared memory but parallel execution.
        You may find:
        - Inconsistent state due to timing issues
        - Overwritten or conflicting information
        - Memory corruption from concurrent access
        - Agents working with outdated context
        
        Original task: {task}
        Shared context: {context}
        Subtask results:
        {results}
        
        Instructions:
        1. Consider the shared context and conversation history
        2. Synthesize all subtask results into a coherent final result
        3. Resolve any inconsistencies from parallel execution
        4. Ensure the final result addresses the original task completely
        5. Create a well-structured, professional output
        
        Final result:
        """,
        input_variables=["task", "context", "results"]
    )
    
    merge_chain = LLMChain(llm=llm, prompt=merge_prompt)
    
    # Format results for the prompt
    results_text = ""
    for agent_id, result in state["sub_results"].items():
        results_text += f"\nAgent {agent_id}:\n{result}\n"
    
    final_result = merge_chain.run(
        task=state["task"],
        context=state.get("context", ""),
        results=results_text
    )
    
    state["final_result"] = final_result
    state["step"] = "results_merged"
    
    return state

def create_parallel_shared_graph():
    """Create a parallel shared graph with shared memory."""
    
    workflow = StateGraph(AgentState)
    
    # Shared memory system - PROBLEM: Shared but still parallel execution
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

def main():
    """Demonstrate Pattern 2: Parallel with Shared Context."""
    
    print("=== PATTERN 2: PARALLEL WITH SHARED CONTEXT (STILL UNRELIABLE) ===\n")
    print("This pattern demonstrates problems with shared memory in parallel execution:")
    print("❌ Timing issues with shared memory access")
    print("❌ Memory corruption from concurrent writes")
    print("❌ Race conditions in memory updates")
    print("❌ Agents can see each other's work but execution is still parallel")
    print("❌ Inconsistent state due to parallel execution\n")
    
    # Example task
    task = "Create a comprehensive marketing strategy for a new mobile app"
    print(f"Task: {task}\n")
    
    try:
        # Create and execute graph
        graph = create_parallel_shared_graph()
        
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
        
        print("Executing parallel shared context pattern...")
        result = graph.invoke(initial_state)
        
        # Display results
        print(f"\nSubtasks created: {len(result['subtasks'])}")
        for i, subtask in enumerate(result['subtasks'], 1):
            print(f"  {i}. {subtask}")
        
        print(f"\nFinal Result Preview:")
        preview = result['final_result'][:300] + "..." if len(result['final_result']) > 300 else result['final_result']
        print(preview)
        
        print(f"\n=== PATTERN 2 ANALYSIS ===")
        print("Problems observed:")
        print("- Agents had shared memory but parallel execution")
        print("- Potential for memory corruption from concurrent access")
        print("- Race conditions in memory updates")
        print("- Inconsistent state due to timing issues")
        print("- Shared context but no coordination")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()