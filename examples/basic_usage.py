"""
Basic usage example for the Multi-Agent Task Breakdown system.
Demonstrates how to use different patterns for task execution.
"""

import os
from dotenv import load_dotenv

from src.multi_agent_task_breakdown import MultiAgentOrchestrator

# Load environment variables
load_dotenv()


def main():
    """Main example function."""
    
    # Example task
    task = "Create a comprehensive marketing strategy for a new mobile app"
    
    print("=== Multi-Agent Task Breakdown Example ===\n")
    print(f"Task: {task}\n")
    
    # Test different patterns
    patterns = [
        "sequential_reliable",
        "sequential_compressed", 
        "parallel_unreliable",
        "parallel_shared"
    ]
    
    for pattern in patterns:
        print(f"--- Testing Pattern: {pattern} ---")
        
        try:
            # Create orchestrator
            orchestrator = MultiAgentOrchestrator(pattern=pattern)
            
            # Get pattern info
            info = orchestrator.get_pattern_info()
            print(f"Pattern: {info.get('name', pattern)}")
            print(f"Description: {info.get('description', 'N/A')}")
            print(f"Memory: {info.get('memory', 'N/A')}")
            print(f"Reliability: {info.get('reliability', 'N/A')}")
            
            # Execute task
            print("\nExecuting task...")
            result = orchestrator.execute_task(task)
            
            # Display results
            print(f"\nSubtasks created: {len(result['subtasks'])}")
            for i, subtask in enumerate(result['subtasks'], 1):
                print(f"  {i}. {subtask}")
            
            print(f"\nFinal Result Preview:")
            preview = result['final_result'][:200] + "..." if len(result['final_result']) > 200 else result['final_result']
            print(preview)
            
        except Exception as e:
            print(f"Error with pattern {pattern}: {e}")
        
        print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    main()