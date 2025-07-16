"""
Compare All Patterns Side by Side
Runs all four agent coordination patterns on the same task to demonstrate their differences.

This script clearly shows the pros and cons of each approach.
"""

import os
import time
from dotenv import load_dotenv

# Import all pattern examples
from pattern1_parallel_unreliable import create_parallel_unreliable_graph
from pattern2_parallel_shared import create_parallel_shared_graph
from pattern3_sequential_reliable import create_sequential_reliable_graph
from pattern4_sequential_compressed import create_sequential_compressed_graph

# Load environment variables
load_dotenv()

def run_pattern_comparison():
    """Run all patterns and compare their results."""
    
    print("=== MULTI-AGENT PATTERN COMPARISON ===\n")
    
    # Example task
    task = "Create a comprehensive marketing strategy for a new mobile app"
    print(f"Task: {task}\n")
    
    # Pattern configurations
    patterns = [
        {
            "name": "Pattern 1: Parallel Unreliable",
            "description": "Isolated agents, no coordination",
            "pros": ["Fast execution", "Simple implementation"],
            "cons": ["Race conditions", "No shared context", "Inconsistent results"],
            "graph_func": create_parallel_unreliable_graph,
            "color": "❌"
        },
        {
            "name": "Pattern 2: Parallel Shared",
            "description": "Shared memory, minimal coordination",
            "pros": ["Shared context", "Faster than sequential"],
            "cons": ["Timing issues", "Memory corruption", "Race conditions"],
            "graph_func": create_parallel_shared_graph,
            "color": "⚠️"
        },
        {
            "name": "Pattern 3: Sequential Reliable",
            "description": "Full coordination, deterministic execution",
            "pros": ["Deterministic", "Full coordination", "Consistent results", "No race conditions"],
            "cons": ["Slower execution", "No parallelization"],
            "graph_func": create_sequential_reliable_graph,
            "color": "✅"
        },
        {
            "name": "Pattern 4: Sequential Compressed",
            "description": "Full coordination with memory optimization",
            "pros": ["Scalable", "Memory efficient", "Production ready", "Cost optimized"],
            "cons": ["Complex implementation", "Overhead for short tasks"],
            "graph_func": create_sequential_compressed_graph,
            "color": "🚀"
        }
    ]
    
    results = {}
    
    for pattern in patterns:
        print(f"{'='*60}")
        print(f"{pattern['color']} {pattern['name']}")
        print(f"{'='*60}")
        print(f"Description: {pattern['description']}")
        print(f"Pros: {', '.join(pattern['pros'])}")
        print(f"Cons: {', '.join(pattern['cons'])}")
        print()
        
        try:
            # Create and execute graph
            graph = pattern['graph_func']()
            
            # Initialize state
            from pattern1_parallel_unreliable import AgentState  # Import from any pattern file
            
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
            
            # Time the execution
            start_time = time.time()
            result = graph.invoke(initial_state)
            execution_time = time.time() - start_time
            
            # Store results
            results[pattern['name']] = {
                'execution_time': execution_time,
                'subtasks_count': len(result['subtasks']),
                'final_result_length': len(result['final_result']),
                'context_length': len(result.get('context', '')),
                'compressed_context_length': len(result.get('compressed_context', '')),
                'step': result['step']
            }
            
            # Display results
            print(f"Execution time: {execution_time:.2f} seconds")
            print(f"Subtasks created: {len(result['subtasks'])}")
            for i, subtask in enumerate(result['subtasks'], 1):
                print(f"  {i}. {subtask}")
            
            print(f"\nFinal Result Preview:")
            preview = result['final_result'][:200] + "..." if len(result['final_result']) > 200 else result['final_result']
            print(preview)
            
            if result.get('compressed_context'):
                print(f"\nCompressed context length: {len(result['compressed_context'])} characters")
            
        except Exception as e:
            print(f"Error: {e}")
            results[pattern['name']] = {'error': str(e)}
        
        print("\n")
    
    # Summary comparison
    print(f"{'='*80}")
    print("SUMMARY COMPARISON")
    print(f"{'='*80}")
    
    print(f"{'Pattern':<35} {'Time (s)':<10} {'Subtasks':<10} {'Result Len':<12} {'Context Len':<12}")
    print("-" * 80)
    
    for pattern in patterns:
        name = pattern['name']
        if name in results and 'error' not in results[name]:
            r = results[name]
            print(f"{name:<35} {r['execution_time']:<10.2f} {r['subtasks_count']:<10} {r['final_result_length']:<12} {r['context_length']:<12}")
        else:
            error = results.get(name, {}).get('error', 'Unknown error')
            print(f"{name:<35} {'ERROR':<10} {'-':<10} {'-':<12} {'-':<12}")
    
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS")
    print(f"{'='*80}")
    print("✅ Pattern 3 (Sequential Reliable): Use for most applications")
    print("🚀 Pattern 4 (Sequential Compressed): Use for long tasks and production")
    print("⚠️  Pattern 2 (Parallel Shared): Avoid - still unreliable")
    print("❌ Pattern 1 (Parallel Unreliable): Avoid - problematic")
    
    print(f"\n{'='*80}")
    print("KEY INSIGHTS")
    print(f"{'='*80}")
    print("• Parallel execution doesn't guarantee better results")
    print("• Coordination is more important than speed for quality")
    print("• Sequential patterns provide consistent, reliable results")
    print("• Memory optimization becomes crucial for long tasks")
    print("• Choose pattern based on task requirements, not just speed")

if __name__ == "__main__":
    run_pattern_comparison()