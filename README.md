# Multi-Agent Task Breakdown with LangChain/LangGraph

A comprehensive system for breaking down complex tasks into subtasks and executing them using different coordination patterns with AWS Bedrock integration and advanced memory management.

## Features

- **4 Different Coordination Patterns**: From unreliable parallel execution to reliable sequential with compression
- **Advanced Memory Management**: Episodic and semantic memory with hot/background processing
- **AWS Bedrock Integration**: Uses Claude Sonnet 3.5 and Titan embeddings
- **LangGraph Workflows**: Visual workflow representation with state management
- **Production Ready**: Error handling, monitoring hooks, and scalable architecture
- **Self-Contained Examples**: Each example is complete and runnable independently

## Architecture

### Tech Stack
- **LLM**: AWS Bedrock Claude Sonnet 3.5
- **Framework**: LangChain + LangGraph
- **Memory**: Advanced episodic and semantic memory system
- **State Management**: LangGraph state management
- **Orchestration**: LangGraph workflow graphs

### Patterns

1. **Parallel Agents (Unreliable)**: Isolated agents, no coordination
2. **Parallel with Shared Context**: Shared memory, minimal coordination
3. **Sequential Agents (Reliable)**: Full coordination, deterministic execution
4. **Sequential with Compression**: Scalable with memory optimization

### Enhanced Memory System

The system implements an advanced memory architecture based on the CoALA (Cognitive Architecture for Language Agents) framework:

#### Episodic Memory
- **Purpose**: Stores specific experiences and interactions
- **Features**: Real-time hot updates, temporal search, contextual retrieval
- **Benefits**: Preserves detailed task execution history

#### Semantic Memory
- **Purpose**: Stores abstract knowledge and patterns
- **Features**: Background consolidation, pattern recognition, knowledge graphs
- **Benefits**: Builds understanding across multiple task executions

## Installation

This project uses `uv` for Python virtual environment and package management.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize project and install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

## Configuration

Create a `.env` file with your AWS credentials:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

## Usage

### Examples

All examples are self-contained and can be run independently. Each example demonstrates different aspects of the multi-agent system:

```bash
# Enhanced memory management examples (recommended for production)
python examples/pattern3_sequential_reliable_enhanced.py    # Sequential with episodic/semantic memory
python examples/pattern4_sequential_compressed_enhanced.py  # Sequential with compression + hot/background updates

# Basic pattern demonstrations
python examples/pattern1_parallel_unreliable.py      # Shows problems with isolated agents
python examples/pattern2_parallel_shared.py          # Shows issues with shared memory in parallel
python examples/pattern3_sequential_reliable.py      # Shows benefits of full coordination
python examples/pattern4_sequential_compressed.py    # Shows memory optimization for long tasks

# Compare all patterns side by side
python examples/compare_all_patterns.py              # Comprehensive comparison

# Basic examples (legacy patterns)
python examples/basic_usage.py                       # Basic patterns without advanced memory
python examples/with_memory_persistence.py           # Basic memory persistence with ChromaDB
```

### Example Structure

Each example is completely self-contained and includes:

- **AWS Bedrock setup** with proper imports
- **Pattern implementation** with LangGraph workflows
- **State management** with TypedDict schemas
- **Memory systems** (where applicable)
- **Complete execution flow** from task breakdown to final result

### Running Examples

```python
# Each example can be run directly
python examples/pattern3_sequential_reliable_enhanced.py

# Examples will prompt for AWS credentials if not configured
# They demonstrate the full workflow from task input to final result
```

## Pattern Comparison

| Pattern | Memory | Coordination | Reliability | Use Case |
|---------|--------|--------------|-------------|----------|
| Parallel Unreliable | Isolated | None | Low | Quick prototypes |
| Parallel Shared | Shared | Minimal | Low | Simple parallel tasks |
| Sequential Reliable | Cumulative | Full | High | Most applications |
| Sequential Compressed | Optimized | Full | High | Long tasks, production |
| **Enhanced Patterns** | **Episodic + Semantic** | **Full + Memory** | **High** | **Production + Knowledge** |

## Memory Management

### Enhanced Memory Architecture

#### Episodic Memory
- **Real-time Updates**: Hot processing during task execution
- **Temporal Search**: Find relevant experiences by time and context
- **Metadata Storage**: Rich context with timestamps and relationships
- **Retrieval**: Semantic similarity search with temporal filtering

#### Semantic Memory
- **Background Processing**: Consolidation of knowledge patterns
- **Pattern Recognition**: Automatic identification of recurring themes
- **Knowledge Graphs**: Hierarchical organization of abstract concepts
- **Cross-Task Learning**: Knowledge transfer between different task types

#### Memory Operations
- **Hot Updates**: Immediate episodic memory updates during execution
- **Background Consolidation**: Asynchronous semantic memory processing
- **Intelligent Retrieval**: Multi-source context retrieval (episodic + semantic + compressed)
- **Compression Integration**: Memory-driven context compression

### Traditional Memory (Legacy Patterns)
- **Short-term**: Conversation buffer for immediate context
- **Long-term**: Vector store with FAISS for semantic search
- **Persistence**: ChromaDB for cross-session memory

## Development

### Project Structure
```
examples/
├── pattern1_parallel_unreliable.py      # Basic parallel pattern
├── pattern2_parallel_shared.py          # Parallel with shared memory
├── pattern3_sequential_reliable.py      # Basic sequential pattern
├── pattern4_sequential_compressed.py    # Sequential with compression
├── pattern3_sequential_reliable_enhanced.py    # Enhanced with episodic/semantic memory
├── pattern4_sequential_compressed_enhanced.py  # Enhanced with compression + memory
├── compare_all_patterns.py              # Pattern comparison
├── basic_usage.py                       # Basic patterns demonstration
└── with_memory_persistence.py           # Memory persistence example
```

### Adding New Patterns

1. Create a new self-contained example file in `examples/`
2. Implement the complete pattern with all necessary imports
3. Include AWS Bedrock setup and configuration
4. Add comprehensive documentation and comments
5. Update the comparison script if needed

### Testing

```bash
# Code formatting
uv run black examples/
uv run isort examples/

# Type checking
uv run mypy examples/
```

## Production Deployment

### Recommended Pattern
Use **Pattern 3 Enhanced (Sequential Reliable with Advanced Memory)** for most applications, upgrading to **Pattern 4 Enhanced (Sequential Compressed with Advanced Memory)** when dealing with:
- Long-running tasks (>10 steps)
- Complex multi-turn conversations
- Memory-intensive workflows
- Production deployments requiring cost optimization
- Applications requiring knowledge retention and pattern recognition

### Enhanced Pattern Benefits
- **Context Retention**: Episodic memory preserves specific experiences
- **Knowledge Consolidation**: Semantic memory builds abstract understanding
- **Efficiency**: Intelligent compression reduces token usage
- **Scalability**: Background processing handles memory management overhead

### Environment Variables
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v1
```

### Monitoring
The system includes hooks for:
- Execution step tracking
- Memory usage monitoring
- Error recovery mechanisms
- Cost optimization
- Memory performance metrics

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the examples in the `examples/` directory
2. Review the SPEC.md for detailed technical specifications
3. Open an issue on GitHub
