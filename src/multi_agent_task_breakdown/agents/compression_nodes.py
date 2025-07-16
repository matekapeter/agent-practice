"""
Compression nodes for Pattern 4: Sequential with Compression.
Implements context compression and compressed agent execution.
"""

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from ..config import config
from ..state import AgentState


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
    
    compression_chain = LLMChain(
        llm=config.llm,
        prompt=compression_prompt
    )
    
    compressed = compression_chain.run(context=state.get("context", ""))
    state["compressed_context"] = compressed
    
    # Store in long-term memory
    config.long_term_memory.save_context(
        inputs={"context": state.get("context", "")},
        outputs={"compressed": compressed}
    )
    
    return state


def compressed_agent_node(state: AgentState, agent_id: str) -> AgentState:
    """Execute a subtask with compressed context and long-term memory retrieval."""
    
    # Retrieve relevant context from long-term memory
    relevant_context = config.long_term_memory.load_memory_variables({
        "query": state["subtasks"][int(agent_id) - 1]
    })["relevant_context"]
    
    agent_prompt = PromptTemplate(
        template="""
        You are Sub-agent {agent_id}. You are working on a specific subtask as part of a larger project.
        
        Compressed context: {compressed_context}
        Relevant history: {relevant_context}
        Current task: {task}
        
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
    
    agent_chain = LLMChain(
        llm=config.llm,
        prompt=agent_prompt
    )
    
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
    
    merge_chain = LLMChain(
        llm=config.llm,
        prompt=merge_prompt
    )
    
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