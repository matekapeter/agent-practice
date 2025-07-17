# Multi-Agent Task Breakdown Documentation

This documentation explains the inner workings of each example in the Multi-Agent Task Breakdown system, with ASCII visualizations showing component interactions and data flow patterns.

## 📚 Documentation Index

### Core Concepts
- [**Architecture Overview**](./01_architecture_overview.md) - System architecture and tech stack
- [**Memory Systems**](./02_memory_systems.md) - Episodic and semantic memory architecture
- [**State Management**](./03_state_management.md) - LangGraph state handling

### Coordination Patterns
- [**Pattern 1: Parallel Unreliable**](./04_pattern1_parallel_unreliable.md) - Isolated agents, no coordination
- [**Pattern 2: Parallel Shared**](./05_pattern2_parallel_shared.md) - Shared memory, minimal coordination  
- [**Pattern 3: Sequential Reliable**](./06_pattern3_sequential_reliable.md) - Full coordination, deterministic execution
- [**Pattern 4: Sequential Compressed**](./07_pattern4_sequential_compressed.md) - Memory-optimized sequential execution

### Enhanced Features
- [**Enhanced Memory Management**](./08_enhanced_memory.md) - Advanced episodic/semantic memory
- [**Memory Persistence**](./09_memory_persistence.md) - Cross-session memory storage
- [**Pattern Comparison**](./10_pattern_comparison.md) - Side-by-side pattern analysis

### Examples Guide
- [**Basic Usage**](./11_basic_usage.md) - Getting started with the system
- [**Running Examples**](./12_running_examples.md) - How to execute each example

## 🎯 Quick Reference

### When to Use Each Pattern

```
Pattern 1 (Parallel Unreliable)    ❌ NOT RECOMMENDED
├── Use Case: Research/prototyping only
├── Pros: Fast, simple
└── Cons: Race conditions, inconsistent results

Pattern 2 (Parallel Shared)        ⚠️  USE WITH CAUTION
├── Use Case: Non-critical tasks with speed requirements
├── Pros: Shared context, faster than sequential
└── Cons: Timing issues, memory corruption

Pattern 3 (Sequential Reliable)    ✅ RECOMMENDED
├── Use Case: Most production applications
├── Pros: Deterministic, consistent, reliable
└── Cons: No parallelization

Pattern 4 (Sequential Compressed)  🚀 PRODUCTION READY
├── Use Case: Large-scale production systems
├── Pros: Scalable, memory-efficient, cost-optimized
└── Cons: Complex implementation
```

### System Flow Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  Task Planner   │───▶│   Subtasks      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Final Result   │◀───│   Aggregator    │◀───│  Agent Execution│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                               ┌─────────────────┐    ┌─────────────────┐
                               │  Memory System  │◀───│   Context Mgmt  │
                               └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

- **LLM**: AWS Bedrock Claude Sonnet 3.5
- **Framework**: LangChain + LangGraph
- **Memory**: FAISS for vector storage, ChromaDB for persistence
- **State Management**: LangGraph StateGraph
- **Embeddings**: Amazon Titan Text Embeddings

## 📖 Reading Guide

1. Start with [Architecture Overview](./01_architecture_overview.md) to understand the system design
2. Read [Memory Systems](./02_memory_systems.md) to understand the advanced memory architecture  
3. Choose your coordination pattern based on your use case:
   - For learning: Start with [Pattern 3 (Sequential Reliable)](./06_pattern3_sequential_reliable.md)
   - For production: Focus on [Pattern 4 (Sequential Compressed)](./07_pattern4_sequential_compressed.md)
4. Explore [Enhanced Memory Management](./08_enhanced_memory.md) for advanced features
5. Use [Pattern Comparison](./10_pattern_comparison.md) to understand trade-offs

Each documentation file includes:
- 🎯 **Purpose**: What the component/pattern does
- 🔧 **How it Works**: Technical implementation details
- 📊 **ASCII Diagrams**: Visual representation of data flow
- ⚡ **Key Features**: Important capabilities
- ⚠️ **Trade-offs**: Pros and cons
- 💡 **Use Cases**: When to use this approach