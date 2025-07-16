"""
Example with memory persistence using ChromaDB.
Demonstrates how to use persistent memory across sessions.

This example shows basic memory persistence without advanced memory management.
For production use, see the enhanced examples with episodic/semantic memory.
"""

import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory, VectorStoreRetrieverMemory
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

def setup_persistent_memory():
    """Setup persistent memory with ChromaDB."""
    
    # Create persistent store
    persistent_store = Chroma(
        persist_directory="./agent_memory",
        embedding_function=embeddings
    )
    
    # Create long-term memory
    long_term_memory = VectorStoreRetrieverMemory(
        retriever=persistent_store.as_retriever(),
        memory_key="historical_context"
    )
    
    return persistent_store, long_term_memory

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

def agent_with_memory_node(state: AgentState, agent_id: str, long_term_memory) -> AgentState:
    """Agent node with memory retrieval."""
    
    # Retrieve relevant historical context
    try:
        memory_vars = long_term_memory.load_memory_variables({
            "query": state["subtasks"][int(agent_id)-1]
        })
        historical_context = memory_vars.get("historical_context", "")
    except Exception:
        historical_context = ""
    
    agent_prompt = PromptTemplate(
        template="""
        You are Sub-agent {agent_id}.
        
        Previous context: {context}
        Historical context: {historical_context}
        Current task: {task}
        
        Use the historical context to inform your response.
        Complete your task and provide a detailed response.
        """,
        input_variables=["agent_id", "context", "historical_context", "task"]
    )
    
    agent_chain = LLMChain(llm=llm, prompt=agent_prompt)
    result = agent_chain.run(
        agent_id=agent_id,
        context=state.get("context", ""),
        historical_context=historical_context,
        task=state["subtasks"][int(agent_id)-1]
    )
    
    state["sub_results"][agent_id] = result
    state["context"] += f"\n[Agent {agent_id}]: {result}"
    state["step"] = f"agent_{agent_id}_completed"
    
    # Save to memory
    long_term_memory.save_context(
        inputs={"task": state["subtasks"][int(agent_id)-1]},
        outputs={"result": result, "context": state["context"]}
    )
    
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

def create_sequential_with_memory_graph(long_term_memory):
    """Create a sequential graph with memory."""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("task_breaker", break_task_node)
    workflow.add_node("agent_1", lambda state: agent_with_memory_node(state, "1", long_term_memory))
    workflow.add_node("agent_2", lambda state: agent_with_memory_node(state, "2", long_term_memory))
    workflow.add_node("merger", merge_results_node)
    
    workflow.set_entry_point("task_breaker")
    workflow.add_edge("task_breaker", "agent_1")
    workflow.add_edge("agent_1", "agent_2")
    workflow.add_edge("agent_2", "merger")
    workflow.add_edge("merger", END)
    
    return workflow.compile()

def execute_task_with_memory(task: str, long_term_memory) -> AgentState:
    """Execute a task using memory persistence."""
    
    # Create graph
    graph = create_sequential_with_memory_graph(long_term_memory)
    
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

def main():
    """Main example with persistent memory."""
    
    print("=== Multi-Agent with Persistent Memory Example ===\n")
    
    # Setup persistent memory
    print("Setting up persistent memory...")
    persistent_store, long_term_memory = setup_persistent_memory()
    
    # Example tasks that build upon each other
    tasks = [
        "Research the latest trends in mobile app development",
        "Create a technical architecture for a mobile app",
        "Design the user interface and user experience",
        "Plan the marketing and launch strategy"
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n--- Task {i}: {task} ---")
        
        try:
            # Execute task
            print("Executing task...")
            result = execute_task_with_memory(task, long_term_memory)
            
            # Display results
            print(f"Subtasks created: {len(result['subtasks'])}")
            for j, subtask in enumerate(result['subtasks'], 1):
                print(f"  {j}. {subtask}")
            
            print(f"\nFinal Result Preview:")
            preview = result['final_result'][:300] + "..." if len(result['final_result']) > 300 else result['final_result']
            print(preview)
            
            # Show that memory is being used
            try:
                memory_vars = long_term_memory.load_memory_variables({"query": task})
                if memory_vars.get("historical_context"):
                    print(f"\nHistorical context retrieved: {len(memory_vars['historical_context'])} characters")
            except Exception as e:
                print(f"Memory retrieval note: {e}")
            
        except Exception as e:
            print(f"Error with task {i}: {e}")
        
        print("\n" + "-"*50)
    
    print("\n=== Memory Persistence Complete ===")
    print("Memory has been saved to ./agent_memory/")
    print("You can restart the application and the memory will persist.")


if __name__ == "__main__":
    main()