"""
Command-line interface for the Multi-Agent Task Breakdown system.
"""

import argparse
import sys
from typing import Optional

from .orchestrator import MultiAgentOrchestrator, PatternType


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Task Breakdown with LangChain/LangGraph"
    )
    
    parser.add_argument(
        "task",
        help="The task to execute"
    )
    
    parser.add_argument(
        "--pattern",
        "-p",
        choices=["parallel_unreliable", "parallel_shared", "sequential_reliable", "sequential_compressed"],
        default="sequential_reliable",
        help="Pattern to use for task execution (default: sequential_reliable)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--show-info",
        "-i",
        action="store_true",
        help="Show pattern information"
    )
    
    args = parser.parse_args()
    
    try:
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator(pattern=args.pattern)
        
        # Show pattern info if requested
        if args.show_info:
            info = orchestrator.get_pattern_info()
            print(f"Pattern: {info.get('name', args.pattern)}")
            print(f"Description: {info.get('description', 'N/A')}")
            print(f"Memory: {info.get('memory', 'N/A')}")
            print(f"Coordination: {info.get('coordination', 'N/A')}")
            print(f"Reliability: {info.get('reliability', 'N/A')}")
            print()
        
        if args.verbose:
            print(f"Executing task: {args.task}")
            print(f"Using pattern: {args.pattern}")
            print()
        
        # Execute task
        result = orchestrator.execute_task(args.task)
        
        # Display results
        print("=== TASK BREAKDOWN ===")
        print(f"Original task: {result['task']}")
        print(f"Subtasks created: {len(result['subtasks'])}")
        
        for i, subtask in enumerate(result['subtasks'], 1):
            print(f"  {i}. {subtask}")
        
        print("\n=== FINAL RESULT ===")
        print(result['final_result'])
        
        if args.verbose:
            print(f"\n=== EXECUTION INFO ===")
            print(f"Final step: {result['step']}")
            print(f"Context length: {len(result.get('context', ''))}")
            print(f"Compressed context length: {len(result.get('compressed_context', ''))}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()