"""
Pattern 3: Sequential Agents with Episodic/Semantic Memory (Reliable)
Demonstrates sequential execution with enhanced memory management.

ADVANTAGES THIS PATTERN SHOWS:
- Deterministic execution order
- Full coordination with memory-enhanced context
- Episodic memory for successful action patterns
- Semantic memory for facts and user preferences
- Learning from past interactions
- Personalized responses based on user history

This is the recommended pattern for most applications with enhanced memory.
"""

import os
import uuid
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

def memory_enhanced_agent_node(state: AgentState, agent_id: str) -> AgentState:
    """Agent with episodic and semantic memory integration"""
    
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
    
    enhanced_prompt = PromptTemplate(
        template="""
        You are Sub-agent {agent_id}.
        
        TASK: {task}
        
        SEMANTIC MEMORY (Known Facts):
        {semantic_context}
        
        EPISODIC MEMORY (Successful Patterns):
        {few_shot_examples}
        
        CURRENT CONTEXT: {context}
        
        ADVANTAGE: You have access to:
        - Semantic facts about user preferences and domain knowledge
        - Episodic memory of successful action patterns
        - Full context from previous agents
        
        Instructions:
        1. Review the semantic facts and episodic patterns
        2. Follow proven successful patterns where applicable
        3. Use semantic facts to personalize your approach
        4. Build upon the work of previous agents
        5. Focus on your assigned subtask
        6. Provide detailed, actionable results
        7. Ensure your work integrates well with previous results
        
        Your response:
        """,
        input_variables=["agent_id", "task", "semantic_context", "few_shot_examples", "context"]
    )
    
    context_chain = LLMChain(
        llm=llm,
        memory=ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        ),
        prompt=enhanced_prompt
    )
    
    task_index = int(agent_id) - 1
    if task_index < len(state["subtasks"]):
        result = context_chain.run(
            agent_id=agent_id,
            task=state["subtasks"][task_index],
            semantic_context=semantic_context,
            few_shot_examples=few_shot_examples,
            context=state.get("context", "")
        )
        
        # Track actions in current episode
        action = f"Agent {agent_id}: {state['subtasks'][task_index]}"
        state["current_episode"]["actions"].append(action)
        
        # Update state with cumulative context
        state["sub_results"][agent_id] = result
        state["context"] += f"\n[Agent {agent_id}]: {result}"
        state["step"] = f"agent_{agent_id}_completed"
    
    return state

def memory_enhanced_merge_node(state: AgentState) -> AgentState:
    """Merge results with full sequential context and memory consideration."""
    
    merge_prompt = PromptTemplate(
        template="""
        You are a result merger with access to memory of successful patterns.
        
        ADVANTAGE: These results were created sequentially with full coordination and memory integration.
        This means:
        - Each agent built upon previous work
        - Agents used semantic facts and episodic patterns
        - No duplicate or contradictory information
        - Consistent approach throughout
        - Cohesive final result
        
        Original task: {task}
        Full context: {context}
        Semantic facts used: {semantic_facts}
        Subtask results:
        {results}
        
        Instructions:
        1. Consider the full sequential context and conversation history
        2. Synthesize all subtask results into a coherent final result
        3. Ensure the final result addresses the original task completely
        4. Create a well-structured, professional output
        5. The result should be cohesive since agents worked sequentially with memory
        6. Consider how this result might inform future similar tasks
        
        Final result:
        """,
        input_variables=["task", "context", "semantic_facts", "results"]
    )
    
    merge_chain = LLMChain(llm=llm, prompt=merge_prompt)
    
    # Format results for the prompt
    results_text = ""
    for agent_id, result in state["sub_results"].items():
        results_text += f"\nAgent {agent_id}:\n{result}\n"
    
    final_result = merge_chain.run(
        task=state["task"],
        context=state.get("context", ""),
        semantic_facts=state.get("semantic_facts", []),
        results=results_text
    )
    
    state["final_result"] = final_result
    state["step"] = "results_merged"
    
    return state

def update_memory_node(state: AgentState) -> AgentState:
    """Update episodic and semantic memory based on interaction"""
    
    print("💾 Updating memory with interaction results...")
    
    # Extract semantic facts from conversation (background process)
    conversation_text = f"Task: {state['task']}\nResults: {str(state['sub_results'])}\nFinal: {state['final_result']}"
    
    # Hot path: immediate memory update
    if state.get("user_feedback") == "positive":
        # Store successful episode
        episodic_memory.add_episode(
            actions=state["current_episode"]["actions"],
            outcome=state["final_result"],
            success=True,
            metadata={
                "task": state["task"],
                "user_id": state.get("user_id"),
                "session_id": state.get("session_id"),
                "pattern": "sequential_memory_enhanced"
            }
        )
        print("✅ Stored successful episode in episodic memory")
    
    # Background process: extract semantic facts
    semantic_facts = extract_semantic_facts(conversation_text, state.get("user_id", ""))
    if semantic_facts:
        print(f"📝 Extracted {len(semantic_facts)} semantic facts")
    
    return state

def create_memory_enhanced_sequential_graph():
    """Create a sequential reliable graph with enhanced memory integration."""
    
    workflow = StateGraph(AgentState)
    
    # Memory-enhanced nodes
    workflow.add_node("memory_retrieval", retrieve_memory_node)
    workflow.add_node("task_breaker", memory_enhanced_break_task_node)
    workflow.add_node("agent_1", lambda state: memory_enhanced_agent_node(state, "1"))
    workflow.add_node("agent_2", lambda state: memory_enhanced_agent_node(state, "2"))
    workflow.add_node("merger", memory_enhanced_merge_node)
    workflow.add_node("memory_update", update_memory_node)
    
    # Sequential execution with memory integration
    workflow.set_entry_point("memory_retrieval")
    workflow.add_edge("memory_retrieval", "task_breaker")
    workflow.add_edge("task_breaker", "agent_1")
    workflow.add_edge("agent_1", "agent_2")
    workflow.add_edge("agent_2", "merger")
    workflow.add_edge("merger", "memory_update")
    workflow.add_edge("memory_update", END)
    
    return workflow.compile()

def main():
    """Demonstrate Pattern 3: Sequential with Enhanced Memory."""
    
    print("=== PATTERN 3: SEQUENTIAL AGENTS WITH ENHANCED MEMORY ===\n")
    print("This pattern demonstrates the advantages of sequential execution with memory:")
    print("✅ Deterministic execution order")
    print("✅ Full coordination with memory-enhanced context")
    print("✅ Episodic memory for successful action patterns")
    print("✅ Semantic memory for facts and user preferences")
    print("✅ Learning from past interactions")
    print("✅ Personalized responses based on user history\n")
    
    # Example task
    task = "Create a comprehensive marketing strategy for a new mobile app"
    print(f"Task: {task}\n")
    
    try:
        # Create and execute graph
        graph = create_memory_enhanced_sequential_graph()
        
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
        
        print("Executing sequential memory-enhanced pattern...")
        result = graph.invoke(initial_state)
        
        # Display results
        print(f"\nSubtasks created: {len(result['subtasks'])}")
        for i, subtask in enumerate(result['subtasks'], 1):
            print(f"  {i}. {subtask}")
        
        print(f"\nFinal Result Preview:")
        preview = result['final_result'][:300] + "..." if len(result['final_result']) > 300 else result['final_result']
        print(preview)
        
        print(f"\n=== PATTERN 3 ENHANCED MEMORY ANALYSIS ===")
        print("Advantages observed:")
        print("- Agents worked sequentially with full coordination")
        print("- Episodic memory provided successful action patterns")
        print("- Semantic memory enhanced personalization")
        print("- Each agent built upon previous work")
        print("- Memory was updated with interaction results")
        print("- Deterministic execution order maintained")
        
        # Show memory statistics
        print(f"\nMemory Statistics:")
        print(f"- Episodic memory episodes: {len(episodic_memory.episodes)}")
        print(f"- Semantic facts stored: {len(semantic_memory.facts_store.index_to_docstore_id)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()