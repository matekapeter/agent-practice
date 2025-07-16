#!/usr/bin/env python3
"""
Test script to verify the multi-agent task breakdown system installation.
"""

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        print("Testing imports...")
        
        # Test core imports
        from src.multi_agent_task_breakdown import MultiAgentOrchestrator, AgentState, config
        print("✓ Core imports successful")
        
        # Test pattern imports
        from src.multi_agent_task_breakdown.patterns import (
            create_parallel_unreliable_graph,
            create_parallel_shared_graph,
            create_sequential_reliable_graph,
            create_sequential_compressed_graph,
        )
        print("✓ Pattern imports successful")
        
        # Test agent imports
        from src.multi_agent_task_breakdown.agents.base_nodes import break_task_node
        from src.multi_agent_task_breakdown.agents.compression_nodes import compress_context_node
        print("✓ Agent imports successful")
        
        # Test configuration
        print(f"✓ Configuration loaded - LLM: {config.llm.model_id}")
        print(f"✓ Embeddings: {config.embeddings.model_id}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_orchestrator_creation():
    """Test that orchestrator can be created."""
    try:
        print("\nTesting orchestrator creation...")
        
        from src.multi_agent_task_breakdown import MultiAgentOrchestrator
        
        # Test all patterns
        patterns = ["sequential_reliable", "sequential_compressed", "parallel_unreliable", "parallel_shared"]
        
        for pattern in patterns:
            orchestrator = MultiAgentOrchestrator(pattern=pattern)
            info = orchestrator.get_pattern_info()
            print(f"✓ {pattern}: {info.get('name', pattern)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Orchestrator creation error: {e}")
        return False


def main():
    """Main test function."""
    print("=== Multi-Agent Task Breakdown Installation Test ===\n")
    
    # Test imports
    imports_ok = test_imports()
    
    # Test orchestrator
    orchestrator_ok = test_orchestrator_creation()
    
    print("\n=== Test Results ===")
    if imports_ok and orchestrator_ok:
        print("✓ All tests passed! Installation is successful.")
        print("\nYou can now use the system:")
        print("  python main.py 'Your task here'")
        print("  python examples/basic_usage.py")
    else:
        print("✗ Some tests failed. Please check the installation.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())