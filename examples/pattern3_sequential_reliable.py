"""
Pattern 3: Sequential Agents (Reliable)
Demonstrates sequential execution with full coordination and cumulative context building.

ADVANTAGES THIS PATTERN SHOWS:
- Deterministic execution order
- Full coordination between agents
- Cumulative context building
- Agents can build on previous work
- Consistent and reliable results
- No race conditions or timing issues

This is the recommended pattern for most applications.
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

def sequential_agent_node(state: AgentState, agent_id: str) -> AgentState:
    """Execute a subtask with full context from previous agents."""
    
    # ADVANTAGE: Each agent gets FULL context of previous work
    context_chain = LLMChain(
        llm=llm,
        memory=ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        ),
        prompt=PromptTemplate(
            template="""
            You are Sub-agent {agent_id}. You are working on a specific subtask as part of a larger project.
            
            Previous context: {context}
            Current task: {task}
            
            ADVANTAGE: You have full context from all previous agents.
            This means you can:
            - Build upon previous work
            - Avoid duplicating effort
            - Ensure consistency with earlier decisions
            - Create a cohesive result
            
            Instructions:
            1. Review the previous context carefully
            2. Build upon the work of previous agents
            3. Focus on your assigned subtask
            4. Provide detailed, actionable results
            5. Ensure your work integrates well with previous results
            
            Your response:
            """,
            input_variables=["agent_id", "context", "task"]
        )
    )
    
    task_index = int(agent_id) - 1
    if task_index < len(state["subtasks"]):
        result = context_chain.run(
            agent_id=agent_id,
            context=state.get("context", ""),
            task=state["subtasks"][task_index]
        )
        
        # Update state with cumulative context
        state["sub_results"][agent_id] = result
        state["context"] += f"\n[Agent {agent_id}]: {result}"
        state["step"] = f"agent_{agent_id}_completed"
    
    return state

def merge_sequential_node(state: AgentState) -> AgentState:
    """Merge results with full sequential context."""
    
    merge_prompt = PromptTemplate(
        template="""
        You are a result merger. Combine the following subtask results into a comprehensive final result.
        
        ADVANTAGE: These results were created sequentially with full coordination.
        This means:
        - Each agent built upon previous work
        - No duplicate or contradictory information
        - Consistent approach throughout
        - Cohesive final result
        
        Original task: {task}
        Full context: {context}
        Subtask results:
        {results}
        
        Instructions:
        1. Consider the full sequential context and conversation history
        2. Synthesize all subtask results into a coherent final result
        3. Ensure the final result addresses the original task completely
        4. Create a well-structured, professional output
        5. The result should be cohesive since agents worked sequentially
        
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

def create_sequential_reliable_graph():
    """Create a sequential reliable graph with cumulative context."""
    
    workflow = StateGraph(AgentState)
    
    # Sequential nodes
    workflow.add_node("task_breaker", break_task_node)
    workflow.add_node("agent_1", lambda state: sequential_agent_node(state, "1"))
    workflow.add_node("agent_2", lambda state: sequential_agent_node(state, "2"))
    workflow.add_node("merger", merge_sequential_node)
    
    # Linear execution path - ADVANTAGE: Deterministic order
    workflow.set_entry_point("task_breaker")
    workflow.add_edge("task_breaker", "agent_1")
    workflow.add_edge("agent_1", "agent_2")
    workflow.add_edge("agent_2", "merger")
    workflow.add_edge("merger", END)
    
    return workflow.compile()

def main():
    """Demonstrate Pattern 3: Sequential Reliable."""
    
    print("=== PATTERN 3: SEQUENTIAL AGENTS (RELIABLE) ===\n")
    print("This pattern demonstrates the advantages of sequential execution:")
    print("✅ Deterministic execution order")
    print("✅ Full coordination between agents")
    print("✅ Cumulative context building")
    print("✅ Agents can build on previous work")
    print("✅ Consistent and reliable results")
    print("✅ No race conditions or timing issues\n")
    
    # Example task
    task = "Create a comprehensive marketing strategy for a new mobile app"
    print(f"Task: {task}\n")
    
    try:
        # Create and execute graph
        graph = create_sequential_reliable_graph()
        
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
        
        print("Executing sequential reliable pattern...")
        result = graph.invoke(initial_state)
        
        # Display results
        print(f"\nSubtasks created: {len(result['subtasks'])}")
        for i, subtask in enumerate(result['subtasks'], 1):
            print(f"  {i}. {subtask}")
        
        print(f"\nFinal Result Preview:")
        preview = result['final_result'][:300] + "..." if len(result['final_result']) > 300 else result['final_result']
        print(preview)
        
        print(f"\n=== PATTERN 3 ANALYSIS ===")
        print("Advantages observed:")
        print("- Agents worked sequentially with full coordination")
        print("- Each agent built upon previous work")
        print("- No duplicate or contradictory information")
        print("- Consistent approach throughout")
        print("- Cohesive final result")
        print("- Deterministic execution order")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()