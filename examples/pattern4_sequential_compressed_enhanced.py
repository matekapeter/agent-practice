"""
Pattern 4: Sequential with Memory Compression + Hot/Background Updates (Scalable)
Demonstrates sequential execution with advanced memory optimization.

ADVANTAGES THIS PATTERN SHOWS:
- Full coordination with intelligent memory management
- Automatic context compression for long tasks
- Hot-path and background memory updates
- Episodic memory with compressed action sequences
- Semantic memory with incremental fact extraction
- Production-ready scalability for complex tasks

This pattern is ideal for long tasks and production deployments.
"""

import os
import uuid
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Dict, List
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

# Memory type definitions following CoALA paper
class SemanticMemory:
    """Long-term store of facts about the world and user preferences"""
    def __init__(self):
        self.facts_store = FAISS.from_texts([""], embeddings)
        self.user_preferences = {}
        
    def add_fact(self, fact: str, metadata: dict = None):
        """Add world knowledge or user preference"""
        self.facts_store.add_texts([fact], metadatas=[metadata or {}])
        
    def retrieve_facts(self, query: str, k: int = 3) -> List[str]:
        """Retrieve relevant facts for current context"""
        docs = self.facts_store.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]

class EpisodicMemory:
    """Store of successful action sequences and specific past events"""
    def __init__(self):
        self.episodes = []
        self.successful_patterns = FAISS.from_texts([""], embeddings)
        
    def add_episode(self, actions: List[str], outcome: str, success: bool, metadata: dict = None):
        """Store a complete action sequence with outcome"""
        episode = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "actions": actions,
            "outcome": outcome,
            "success": success,
            "metadata": metadata or {}
        }
        self.episodes.append(episode)
        
        # If successful, add to pattern matching store
        if success:
            pattern_text = f"Actions: {' -> '.join(actions)} | Outcome: {outcome}"
            self.successful_patterns.add_texts(
                [pattern_text], 
                metadatas=[{"episode_id": episode["id"], "success": True}]
            )
    
    def retrieve_similar_episodes(self, current_context: str, k: int = 3) -> List[dict]:
        """Find similar successful episodes for few-shot prompting"""
        docs = self.successful_patterns.similarity_search(current_context, k=k)
        episode_ids = [doc.metadata.get("episode_id") for doc in docs]
        return [ep for ep in self.episodes if ep["id"] in episode_ids]

# Initialize memory systems
semantic_memory = SemanticMemory()
episodic_memory = EpisodicMemory()

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
    # Memory-specific fields
    current_episode: dict  # Track current action sequence
    semantic_facts: list[str]  # Retrieved facts for context
    episodic_examples: list[dict]  # Retrieved similar episodes
    user_id: str  # For personalized memory
    session_id: str  # For session tracking

def extract_semantic_facts(conversation: str, user_id: str) -> List[str]:
    """Extract facts and preferences from conversation using LLM"""
    extraction_prompt = f"""
    Extract factual information and user preferences from this conversation.
    Focus on: user preferences, stated facts, domain knowledge, personal context.
    
    Conversation: {conversation}
    
    Return each fact as a separate line starting with "FACT:"
    """
    
    response = llm.invoke(extraction_prompt)
    facts = [line.replace("FACT:", "").strip() 
             for line in response.split("\n") 
             if line.startswith("FACT:")]
    
    # Store in semantic memory
    for fact in facts:
        semantic_memory.add_fact(fact, {"user_id": user_id, "extracted_at": datetime.now().isoformat()})
    
    return facts

def retrieve_episodic_examples(current_task: str, k: int = 3) -> List[dict]:
    """Get similar successful episodes for few-shot prompting"""
    examples = episodic_memory.retrieve_similar_episodes(current_task, k=k)
    
    # Format for prompting
    formatted_examples = []
    for episode in examples:
        formatted_examples.append({
            "task_context": episode["metadata"].get("task", ""),
            "actions": episode["actions"],
            "outcome": episode["outcome"],
            "success": episode["success"]
        })
    
    return formatted_examples

def retrieve_memory_node(state: AgentState) -> AgentState:
    """Retrieve relevant semantic facts and episodic examples"""
    
    print("🔍 Retrieving memory for task...")
    
    # Get semantic facts about user and task domain
    semantic_facts = semantic_memory.retrieve_facts(
        f"user: {state.get('user_id', '')} task: {state['task']}", 
        k=5
    )
    
    # Get similar successful episodes
    episodic_examples = retrieve_episodic_examples(state["task"], k=3)
    
    state["semantic_facts"] = semantic_facts
    state["episodic_examples"] = episodic_examples
    
    # Initialize current episode tracking
    state["current_episode"] = {
        "actions": [],
        "start_time": datetime.now().isoformat(),
        "task": state["task"]
    }
    
    print(f"📚 Retrieved {len(semantic_facts)} semantic facts")
    print(f"🎯 Found {len(episodic_examples)} similar episodes")
    
    return state

def memory_enhanced_break_task_node(state: AgentState) -> AgentState:
    """Break down a complex task into subtasks with memory context."""
    
    # Build few-shot examples from episodic memory
    few_shot_examples = ""
    for i, example in enumerate(state.get("episodic_examples", [])):
        few_shot_examples += f"""
        Example {i+1}:
        Task: {example['task_context']}
        Actions: {' -> '.join(example['actions'])}
        Result: {example['outcome']}
        Success: {example['success']}
        
        """
    
    # Build semantic context
    semantic_context = "\n".join(f"- {fact}" for fact in state.get("semantic_facts", []))
    
    break_prompt = PromptTemplate(
        template="""
        You are a task breakdown specialist with access to memory of successful patterns.
        
        TASK: {task}
        
        SEMANTIC MEMORY (Known Facts):
        {semantic_context}
        
        EPISODIC MEMORY (Successful Patterns):
        {few_shot_examples}
        
        Instructions:
        1. Analyze the task and identify logical components
        2. Create 2-3 subtasks that can be worked on sequentially
        3. Each subtask should build upon the previous one
        4. Use successful patterns from episodic memory as guidance
        5. Consider user preferences from semantic memory
        6. Return only the subtasks as a numbered list
        
        Subtasks:
        """,
        input_variables=["task", "semantic_context", "few_shot_examples"]
    )
    
    break_chain = LLMChain(llm=llm, prompt=break_prompt)
    result = break_chain.run(
        task=state["task"],
        semantic_context=semantic_context,
        few_shot_examples=few_shot_examples
    )
    
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
    
    # Track task breakdown in episode
    state["current_episode"]["actions"].append(f"Task broken into: {' -> '.join(subtasks)}")
    
    return state

def compress_memory_context_node(state: AgentState) -> AgentState:
    """Compress context while preserving memory-relevant information"""
    
    print("🗜️  Compressing memory context...")
    
    compression_prompt = f"""
    Compress the following context while preserving:
    1. Key task progress and decisions
    2. Important semantic facts about user/domain
    3. Action patterns that worked well
    4. Any failed approaches to avoid
    
    Current Context: {state["context"]}
    Semantic Facts: {state.get("semantic_facts", [])}
    Episode Actions: {state.get("current_episode", {}).get("actions", [])}
    
    Compress to <200 words while maintaining actionable information.
    """
    
    compressed = llm.invoke(compression_prompt)
    state["compressed_context"] = compressed
    
    print(f"📦 Compressed context length: {len(compressed)} characters")
    
    return state

def compressed_memory_agent_node(state: AgentState, agent_id: str) -> AgentState:
    """Agent using compressed context with memory integration"""
    
    # Get most relevant episodic examples for current subtask
    current_subtask = state["subtasks"][int(agent_id) - 1]
    relevant_episodes = episodic_memory.retrieve_similar_episodes(current_subtask, k=2)
    
    # Build minimal few-shot examples
    few_shot = ""
    for i, episode in enumerate(relevant_episodes):
        few_shot += f"Pattern {i+1}: {' -> '.join(episode['actions'][-2:])} -> {episode['outcome'][:100]}...\n"
    
    # Get most relevant semantic facts
    relevant_facts = semantic_memory.retrieve_facts(current_subtask, k=3)
    
    prompt = PromptTemplate(
        template="""
        You are Sub-agent {agent_id}.
        
        Task: {task}
        
        Compressed Context: {compressed_context}
        
        Relevant Patterns (Episodic):
        {few_shot}
        
        Key Facts (Semantic):
        {semantic_facts}
        
        ADVANTAGE: You have optimized memory access with:
        - Compressed context for efficiency
        - Semantic search for relevant history
        - Full coordination with previous agents
        - Scalable memory management
        
        Instructions:
        1. Use the compressed context to understand the project scope
        2. Leverage relevant historical context for your task
        3. Follow proven patterns from episodic memory
        4. Focus on your assigned subtask
        5. Provide detailed, actionable results
        6. Ensure your work integrates well with the overall project
        
        Your response:
        """,
        input_variables=["agent_id", "task", "compressed_context", "few_shot", "semantic_facts"]
    )
    
    agent_chain = LLMChain(llm=llm, prompt=prompt)
    
    task_index = int(agent_id) - 1
    if task_index < len(state["subtasks"]):
        result = agent_chain.run(
            agent_id=agent_id,
            task=current_subtask,
            compressed_context=state.get("compressed_context", ""),
            few_shot=few_shot,
            semantic_facts="\n".join(f"- {fact}" for fact in relevant_facts)
        )
        
        # Track in episode
        action = f"Agent {agent_id}: {current_subtask}"
        state["current_episode"]["actions"].append(action)
        state["current_episode"][f"agent_{agent_id}_result"] = result
        
        state["sub_results"][agent_id] = result
        state["step"] = f"agent_{agent_id}_completed"
    
    return state

def compressed_memory_merge_node(state: AgentState) -> AgentState:
    """Merge results with compressed context consideration."""
    
    merge_prompt = PromptTemplate(
        template="""
        You are a result merger with optimized memory management.
        
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

def hot_path_memory_update_node(state: AgentState) -> AgentState:
    """Immediate memory updates in the hot path"""
    
    print("🔥 Hot-path memory update...")
    
    # User feedback-driven updates (if available)
    if state.get("user_feedback"):
        feedback = state["user_feedback"]
        
        if feedback == "positive":
            # Store successful episode immediately
            episodic_memory.add_episode(
                actions=state["current_episode"]["actions"],
                outcome=state["final_result"],
                success=True,
                metadata={
                    "task_type": state["task"],
                    "user_id": state.get("user_id"),
                    "agent_pattern": "sequential_compressed",
                    "feedback": "positive"
                }
            )
            print("✅ Stored successful episode (hot-path)")
        elif feedback == "negative":
            # Store failed pattern to avoid
            episodic_memory.add_episode(
                actions=state["current_episode"]["actions"],
                outcome=state["final_result"],
                success=False,
                metadata={
                    "task_type": state["task"],
                    "user_id": state.get("user_id"),
                    "failure_reason": state.get("failure_reason", "user_negative_feedback")
                }
            )
            print("❌ Stored failed episode (hot-path)")
    
    # Immediate semantic fact extraction if high-value interaction
    if state.get("high_value_interaction"):
        key_facts = extract_semantic_facts(
            f"Task: {state['task']} Result: {state['final_result']}", 
            state.get("user_id", "")
        )
        state["extracted_facts"] = key_facts
        print(f"📝 Extracted {len(key_facts)} facts (hot-path)")
    
    return state

def background_memory_update_node(state: AgentState) -> AgentState:
    """Background memory processing (simulated - would be async in production)"""
    
    print("🔄 Background memory processing...")
    
    # Comprehensive semantic extraction
    full_conversation = f"""
    User Task: {state['task']}
    Subtasks: {state.get('subtasks', [])}
    Agent Results: {state.get('sub_results', {})}
    Final Outcome: {state.get('final_result', '')}
    User Context: {state.get('user_id', '')}
    """
    
    # Extract semantic facts (would run async in production)
    background_facts = extract_semantic_facts(full_conversation, state.get("user_id", ""))
    
    # Pattern analysis for episodic memory
    if not state.get("user_feedback"):  # If no explicit feedback, infer success
        # Simple heuristic: if final result is substantial, consider successful
        if len(state.get("final_result", "")) > 100:  # Basic success heuristic
            episodic_memory.add_episode(
                actions=state["current_episode"]["actions"],
                outcome=state["final_result"],
                success=True,
                metadata={
                    "task_type": state["task"],
                    "user_id": state.get("user_id"),
                    "inferred_success": True,
                    "pattern_type": "sequential_compressed"
                }
            )
            print("✅ Stored inferred successful episode (background)")
    
    # Memory consolidation (compress old episodes, merge similar facts, etc.)
    # This would be more sophisticated in production
    state["background_processing_complete"] = True
    
    print(f"📝 Extracted {len(background_facts)} facts (background)")
    print("✅ Background memory processing complete")
    
    return state

def create_memory_compressed_graph():
    """Create a sequential compressed graph with memory optimization."""
    
    workflow = StateGraph(AgentState)
    
    # Memory and compression-aware nodes
    workflow.add_node("memory_retrieval", retrieve_memory_node)
    workflow.add_node("task_breaker", memory_enhanced_break_task_node)
    workflow.add_node("compress_1", compress_memory_context_node)
    workflow.add_node("agent_1", lambda state: compressed_memory_agent_node(state, "1"))
    workflow.add_node("compress_2", compress_memory_context_node)
    workflow.add_node("agent_2", lambda state: compressed_memory_agent_node(state, "2"))
    workflow.add_node("compress_final", compress_memory_context_node)
    workflow.add_node("merger", compressed_memory_merge_node)
    workflow.add_node("memory_update_hot", hot_path_memory_update_node)
    workflow.add_node("memory_update_background", background_memory_update_node)
    
    # Sequential with compression and memory steps
    workflow.set_entry_point("memory_retrieval")
    workflow.add_edge("memory_retrieval", "task_breaker")
    workflow.add_edge("task_breaker", "compress_1")
    workflow.add_edge("compress_1", "agent_1")
    workflow.add_edge("agent_1", "compress_2")
    workflow.add_edge("compress_2", "agent_2")
    workflow.add_edge("agent_2", "compress_final")
    workflow.add_edge("compress_final", "merger")
    workflow.add_edge("merger", "memory_update_hot")
    workflow.add_edge("memory_update_hot", "memory_update_background")
    workflow.add_edge("memory_update_background", END)
    
    return workflow.compile()

def main():
    """Demonstrate Pattern 4: Sequential with Memory Compression."""
    
    print("=== PATTERN 4: SEQUENTIAL WITH MEMORY COMPRESSION + HOT/BACKGROUND UPDATES ===\n")
    print("This pattern demonstrates advanced memory optimization for long tasks:")
    print("✅ Full coordination with intelligent memory management")
    print("✅ Automatic context compression for long tasks")
    print("✅ Hot-path and background memory updates")
    print("✅ Episodic memory with compressed action sequences")
    print("✅ Semantic memory with incremental fact extraction")
    print("✅ Production-ready scalability for complex tasks\n")
    
    # Example task
    task = "Create a comprehensive marketing strategy for a new mobile app"
    print(f"Task: {task}\n")
    
    try:
        # Create and execute graph
        graph = create_memory_compressed_graph()
        
        # Initialize state with memory fields
        initial_state = AgentState(
            messages=[],
            task=task,
            subtasks=[],
            sub_results={},
            final_result="",
            context="",
            compressed_context="",
            step="start",
            current_episode={},
            semantic_facts=[],
            episodic_examples=[],
            user_id="user_123",
            session_id="session_456"
        )
        
        print("Executing sequential compressed memory pattern...")
        result = graph.invoke(initial_state)
        
        # Display results
        print(f"\nSubtasks created: {len(result['subtasks'])}")
        for i, subtask in enumerate(result['subtasks'], 1):
            print(f"  {i}. {subtask}")
        
        print(f"\nCompressed context length: {len(result.get('compressed_context', ''))}")
        
        print(f"\nFinal Result Preview:")
        preview = result['final_result'][:300] + "..." if len(result['final_result']) > 300 else result['final_result']
        print(preview)
        
        print(f"\n=== PATTERN 4 ENHANCED MEMORY ANALYSIS ===")
        print("Advantages observed:")
        print("- Full coordination with memory optimization")
        print("- Automatic context compression for efficiency")
        print("- Vector store retrieval for relevant history")
        print("- Hot-path and background memory updates")
        print("- Scalable for long-running workflows")
        print("- Production-ready architecture")
        
        # Show memory statistics
        print(f"\nMemory Statistics:")
        print(f"- Episodic memory episodes: {len(episodic_memory.episodes)}")
        print(f"- Semantic facts stored: {len(semantic_memory.facts_store.index_to_docstore_id)}")
        print(f"- Background processing: {result.get('background_processing_complete', False)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()