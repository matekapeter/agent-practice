"""
Pattern 4: Sequential with Compression (Scalable)
Demonstrates sequential execution with memory optimization via compression.

ADVANTAGES THIS PATTERN SHOWS:
- Full coordination with memory management
- Automatic context compression for long tasks
- Vector store retrieval for relevant history
- Scalable for long-running workflows
- Cost optimization through compression
- Production-ready for complex tasks

This pattern is ideal for long tasks and production deployments.
"""

import os
from dotenv import load_dotenv
from langchain_aws import BedrockLLM
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory, VectorStoreRetrieverMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

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

# Memory systems
short_term_memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

vector_store = FAISS.from_texts([""], embeddings)
long_term_memory = VectorStoreRetrieverMemory(
    retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
    memory_key="relevant_context"
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
        2. Create 2-3 subtasks that can be worked on sequentially
        3. Each subtask should build upon the previous one
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

def compress_context_node(state: AgentState) -> AgentState:
    """Compress the current context into key insights."""
    
    compression_prompt = PromptTemplate(
        template="""
        Compress the following context into key insights (<200 words):
        
        Context: {context}
        
        Instructions:
        1. Preserve: Task goals, completed work, key decisions
        2. Remove: Verbose explanations, redundant information
        3. Focus on actionable insights and important findings
        4. Keep the compression under 200 words
        
        Compressed context:
        """,
        input_variables=["context"]
    )
    
    compression_chain = LLMChain(llm=llm, prompt=compression_prompt)
    
    compressed = compression_chain.run(context=state.get("context", ""))
    state["compressed_context"] = compressed
    
    # Store in long-term memory
    long_term_memory.save_context(
        inputs={"context": state.get("context", "")},
        outputs={"compressed": compressed}
    )
    
    return state

def compressed_agent_node(state: AgentState, agent_id: str) -> AgentState:
    """Execute a subtask with compressed context and long-term memory retrieval."""
    
    # Retrieve relevant context from long-term memory
    relevant_context = long_term_memory.load_memory_variables({
        "query": state["subtasks"][int(agent_id) - 1]
    })["relevant_context"]
    
    agent_prompt = PromptTemplate(
        template="""
        You are Sub-agent {agent_id}. You are working on a specific subtask as part of a larger project.
        
        Compressed context: {compressed_context}
        Relevant history: {relevant_context}
        Current task: {task}
        
        ADVANTAGE: You have optimized memory access with:
        - Compressed context for efficiency
        - Semantic search for relevant history
        - Full coordination with previous agents
        - Scalable memory management
        
        Instructions:
        1. Use the compressed context to understand the project scope
        2. Leverage relevant historical context for your task
        3. Focus on your assigned subtask
        4. Provide detailed, actionable results
        5. Ensure your work integrates well with the overall project
        
        Your response:
        """,
        input_variables=["agent_id", "compressed_context", "relevant_context", "task"]
    )
    
    agent_chain = LLMChain(llm=llm, prompt=agent_prompt)
    
    task_index = int(agent_id) - 1
    if task_index < len(state["subtasks"]):
        result = agent_chain.run(
            agent_id=agent_id,
            compressed_context=state.get("compressed_context", ""),
            relevant_context=relevant_context,
            task=state["subtasks"][task_index]
        )
        
        state["sub_results"][agent_id] = result
        state["step"] = f"agent_{agent_id}_completed"
    
    return state

def merge_compressed_node(state: AgentState) -> AgentState:
    """Merge results with compressed context consideration."""
    
    merge_prompt = PromptTemplate(
        template="""
        You are a result merger. Combine the following subtask results into a comprehensive final result.
        
        ADVANTAGE: These results were created with optimized memory management.
        This means:
        - Efficient context compression
        - Semantic retrieval of relevant history
        - Full coordination with memory optimization
        - Production-ready scalability
        
        Original task: {task}
        Compressed context: {compressed_context}
        Subtask results:
        {results}
        
        Instructions:
        1. Consider the compressed context and project scope
        2. Synthesize all subtask results into a coherent final result
        3. Ensure the final result addresses the original task completely
        4. Create a well-structured, professional output
        5. Maintain the quality and detail from individual subtasks
        
        Final result:
        """,
        input_variables=["task", "compressed_context", "results"]
    )
    
    merge_chain = LLMChain(llm=llm, prompt=merge_prompt)
    
    # Format results for the prompt
    results_text = ""
    for agent_id, result in state["sub_results"].items():
        results_text += f"\nAgent {agent_id}:\n{result}\n"
    
    final_result = merge_chain.run(
        task=state["task"],
        compressed_context=state.get("compressed_context", ""),
        results=results_text
    )
    
    state["final_result"] = final_result
    state["step"] = "results_merged"
    
    return state

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

def main():
    """Demonstrate Pattern 4: Sequential with Compression."""
    
    print("=== PATTERN 4: SEQUENTIAL WITH COMPRESSION (SCALABLE) ===\n")
    print("This pattern demonstrates memory optimization for long tasks:")
    print("✅ Full coordination with memory management")
    print("✅ Automatic context compression for long tasks")
    print("✅ Vector store retrieval for relevant history")
    print("✅ Scalable for long-running workflows")
    print("✅ Cost optimization through compression")
    print("✅ Production-ready for complex tasks\n")
    
    # Example task
    task = "Create a comprehensive marketing strategy for a new mobile app"
    print(f"Task: {task}\n")
    
    try:
        # Create and execute graph
        graph = create_sequential_compressed_graph()
        
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
        
        print("Executing sequential compressed pattern...")
        result = graph.invoke(initial_state)
        
        # Display results
        print(f"\nSubtasks created: {len(result['subtasks'])}")
        for i, subtask in enumerate(result['subtasks'], 1):
            print(f"  {i}. {subtask}")
        
        print(f"\nCompressed context length: {len(result.get('compressed_context', ''))}")
        
        print(f"\nFinal Result Preview:")
        preview = result['final_result'][:300] + "..." if len(result['final_result']) > 300 else result['final_result']
        print(preview)
        
        print(f"\n=== PATTERN 4 ANALYSIS ===")
        print("Advantages observed:")
        print("- Full coordination with memory optimization")
        print("- Automatic context compression for efficiency")
        print("- Vector store retrieval for relevant history")
        print("- Scalable for long-running workflows")
        print("- Cost optimization through compression")
        print("- Production-ready architecture")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()