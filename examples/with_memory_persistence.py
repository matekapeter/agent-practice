"""
Example with memory persistence using ChromaDB.
Demonstrates how to use persistent memory across sessions.
"""

import os
from dotenv import load_dotenv

from langchain.vectorstores import Chroma
from src.multi_agent_task_breakdown import MultiAgentOrchestrator, config

# Load environment variables
load_dotenv()


def setup_persistent_memory():
    """Setup persistent memory with ChromaDB."""
    
    # Create persistent store
    persistent_store = Chroma(
        persist_directory="./agent_memory",
        embedding_function=config.embeddings
    )
    
    # Update the long-term memory to use persistent store
    from langchain.memory import VectorStoreRetrieverMemory
    
    config.long_term_memory = VectorStoreRetrieverMemory(
        retriever=persistent_store.as_retriever(),
        memory_key="historical_context"
    )
    
    return persistent_store


def main():
    """Main example with persistent memory."""
    
    print("=== Multi-Agent with Persistent Memory Example ===\n")
    
    # Setup persistent memory
    print("Setting up persistent memory...")
    persistent_store = setup_persistent_memory()
    
    # Example tasks that build upon each other
    tasks = [
        "Research the latest trends in mobile app development",
        "Create a technical architecture for a mobile app",
        "Design the user interface and user experience",
        "Plan the marketing and launch strategy"
    ]
    
    # Use sequential compressed pattern for best memory utilization
    orchestrator = MultiAgentOrchestrator(pattern="sequential_compressed")
    
    for i, task in enumerate(tasks, 1):
        print(f"\n--- Task {i}: {task} ---")
        
        try:
            # Execute task
            print("Executing task...")
            result = orchestrator.execute_task(task)
            
            # Display results
            print(f"Subtasks created: {len(result['subtasks'])}")
            for j, subtask in enumerate(result['subtasks'], 1):
                print(f"  {j}. {subtask}")
            
            print(f"\nFinal Result Preview:")
            preview = result['final_result'][:300] + "..." if len(result['final_result']) > 300 else result['final_result']
            print(preview)
            
            # Show that memory is being used
            if hasattr(config.long_term_memory, 'load_memory_variables'):
                try:
                    memory_vars = config.long_term_memory.load_memory_variables({"query": task})
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