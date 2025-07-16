"""
Base agent nodes for the multi-agent task breakdown system.
Implements core functionality for task breaking, agent execution, and result merging.
"""

from typing import Any, Dict

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from ..config import config
from ..state import AgentState


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
    
    break_chain = LLMChain(
        llm=config.llm,
        prompt=break_prompt
    )
    
    result = break_chain.run(task=state["task"])
    
    # Parse the result into a list of subtasks
    subtasks = []
    for line in result.strip().split('\n'):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
            # Remove numbering/bullets and clean up
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
    """Execute a subtask with an isolated agent (Pattern 1)."""
    
    # Isolated memory for this agent
    isolated_memory = config.short_term_memory.__class__(
        memory_key="chat_history",
        return_messages=True
    )
    
    agent_prompt = PromptTemplate(
        template="""
        You are Sub-agent {agent_id}. You are working on a specific subtask as part of a larger project.
        
        Your task: {task}
        
        Instructions:
        1. Focus only on your assigned subtask
        2. Provide detailed, actionable results
        3. Be thorough but concise
        4. Consider how your work might integrate with other subtasks
        
        Your response:
        """,
        input_variables=["agent_id", "task"]
    )
    
    chain = LLMChain(
        llm=config.llm,
        memory=isolated_memory,
        prompt=agent_prompt
    )
    
    task_index = int(agent_id) - 1
    if task_index < len(state["subtasks"]):
        result = chain.run(
            agent_id=agent_id,
            task=state["subtasks"][task_index]
        )
        state["sub_results"][agent_id] = result
        state["step"] = f"agent_{agent_id}_completed"
    
    return state


def shared_agent_node(state: AgentState, agent_id: str, shared_memory) -> AgentState:
    """Execute a subtask with shared memory (Pattern 2)."""
    
    agent_prompt = PromptTemplate(
        template="""
        You are Sub-agent {agent_id}. You are working on a specific subtask as part of a larger project.
        
        Shared context: {history}
        Your task: {task}
        
        Instructions:
        1. Consider the shared context from other agents
        2. Focus on your assigned subtask
        3. Provide detailed, actionable results
        4. Build upon or complement work from other agents
        
        Your response:
        """,
        input_variables=["agent_id", "history", "task"]
    )
    
    chain = LLMChain(
        llm=config.llm,
        memory=shared_memory,
        prompt=agent_prompt
    )
    
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


def sequential_agent_node(state: AgentState, agent_id: str) -> AgentState:
    """Execute a subtask with full context (Pattern 3)."""
    
    agent_prompt = PromptTemplate(
        template="""
        You are Sub-agent {agent_id}. You are working on a specific subtask as part of a larger project.
        
        Previous context: {context}
        Your task: {task}
        
        Instructions:
        1. Build upon the previous work and context
        2. Focus on your assigned subtask
        3. Provide detailed, actionable results
        4. Ensure your work integrates well with previous results
        
        Your response:
        """,
        input_variables=["agent_id", "context", "task"]
    )
    
    chain = LLMChain(
        llm=config.llm,
        memory=config.short_term_memory,
        prompt=agent_prompt
    )
    
    task_index = int(agent_id) - 1
    if task_index < len(state["subtasks"]):
        result = chain.run(
            agent_id=agent_id,
            context=state.get("context", ""),
            task=state["subtasks"][task_index]
        )
        
        # Update state with cumulative context
        state["sub_results"][agent_id] = result
        state["context"] += f"\n[Agent {agent_id}]: {result}"
        state["step"] = f"agent_{agent_id}_completed"
    
    return state


def merge_results_node(state: AgentState) -> AgentState:
    """Merge results from all agents into a final result."""
    
    merge_prompt = PromptTemplate(
        template="""
        You are a result merger. Combine the following subtask results into a comprehensive final result.
        
        Original task: {task}
        Subtask results:
        {results}
        
        Instructions:
        1. Synthesize all subtask results into a coherent final result
        2. Ensure the final result addresses the original task completely
        3. Maintain the quality and detail from individual subtasks
        4. Create a well-structured, professional output
        
        Final result:
        """,
        input_variables=["task", "results"]
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
        results=results_text
    )
    
    state["final_result"] = final_result
    state["step"] = "results_merged"
    
    return state


def merge_with_context_node(state: AgentState) -> AgentState:
    """Merge results with shared context consideration."""
    
    merge_prompt = PromptTemplate(
        template="""
        You are a result merger. Combine the following subtask results into a comprehensive final result.
        
        Original task: {task}
        Shared context: {context}
        Subtask results:
        {results}
        
        Instructions:
        1. Consider the shared context and conversation history
        2. Synthesize all subtask results into a coherent final result
        3. Ensure the final result addresses the original task completely
        4. Create a well-structured, professional output
        
        Final result:
        """,
        input_variables=["task", "context", "results"]
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
        context=state.get("context", ""),
        results=results_text
    )
    
    state["final_result"] = final_result
    state["step"] = "results_merged"
    
    return state


def merge_sequential_node(state: AgentState) -> AgentState:
    """Merge results with full sequential context."""
    
    merge_prompt = PromptTemplate(
        template="""
        You are a result merger. Combine the following subtask results into a comprehensive final result.
        
        Original task: {task}
        Full context: {context}
        Subtask results:
        {results}
        
        Instructions:
        1. Consider the full sequential context and conversation history
        2. Synthesize all subtask results into a coherent final result
        3. Ensure the final result addresses the original task completely
        4. Create a well-structured, professional output
        
        Final result:
        """,
        input_variables=["task", "context", "results"]
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
        context=state.get("context", ""),
        results=results_text
    )
    
    state["final_result"] = final_result
    state["step"] = "results_merged"
    
    return state