# Multi-Agent Task Breakdown with LangChain/LangGraph

A comprehensive system for breaking down complex tasks into subtasks and executing them using different coordination patterns with AWS Bedrock integration.

## Features

- **4 Different Coordination Patterns**: From unreliable parallel execution to reliable sequential with compression
- **AWS Bedrock Integration**: Uses Claude Sonnet 3.5 and Titan embeddings
- **Memory Management**: Short-term conversation memory and long-term vector storage
- **LangGraph Workflows**: Visual workflow representation with state management
- **Production Ready**: Error handling, monitoring hooks, and scalable architecture

## Architecture

### Tech Stack
- **LLM**: AWS Bedrock Claude Sonnet 3.5
- **Framework**: LangChain + LangGraph
- **Memory**: Short-term (conversation) + Long-term (vector store)
- **State Management**: LangGraph state management
- **Orchestration**: LangGraph workflow graphs

### Patterns

1. **Parallel Agents (Unreliable)**: Isolated agents, no coordination
2. **Parallel with Shared Context**: Shared memory, minimal coordination
3. **Sequential Agents (Reliable)**: Full coordination, deterministic execution
4. **Sequential with Compression**: Scalable with memory optimization

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

### Command Line Interface

```bash
# Basic usage with default pattern (sequential_reliable)
python main.py "Create a marketing strategy for a mobile app"

# Use specific pattern
python main.py "Design a website" --pattern sequential_compressed

# Verbose output with pattern info
python main.py "Plan a project" --pattern parallel_shared --verbose --show-info
```

### Python API

```python
from src.multi_agent_task_breakdown import MultiAgentOrchestrator

# Create orchestrator with default pattern
orchestrator = MultiAgentOrchestrator()

# Execute a task
result = orchestrator.execute_task("Create a business plan")

# Use different pattern
orchestrator = MultiAgentOrchestrator(pattern="sequential_compressed")
result = orchestrator.execute_task("Design a mobile app")

# Get pattern information
info = orchestrator.get_pattern_info()
print(f"Pattern: {info['name']}")
print(f"Reliability: {info['reliability']}")
```

### Examples

Run the provided examples to see different patterns in action:

```bash
# Enhanced memory management examples (recommended)
python examples/pattern3_sequential_reliable_enhanced.py    # Sequential with episodic/semantic memory
python examples/pattern4_sequential_compressed_enhanced.py  # Sequential with compression + hot/background updates

# Basic pattern demonstrations
python examples/pattern1_parallel_unreliable.py      # Shows problems with isolated agents
python examples/pattern2_parallel_shared.py          # Shows issues with shared memory in parallel
python examples/pattern3_sequential_reliable.py      # Shows benefits of full coordination
python examples/pattern4_sequential_compressed.py    # Shows memory optimization for long tasks

# Compare all patterns side by side
python examples/compare_all_patterns.py              # Comprehensive comparison

# Legacy examples (still available)
python examples/basic_usage.py                       # Basic usage with the unified API
python examples/with_memory_persistence.py           # Memory persistence example
```

## Pattern Comparison

| Pattern | Memory | Coordination | Reliability | Use Case |
|---------|--------|--------------|-------------|----------|
| Parallel Unreliable | Isolated | None | Low | Quick prototypes |
| Parallel Shared | Shared | Minimal | Low | Simple parallel tasks |
| Sequential Reliable | Cumulative | Full | High | Most applications |
| Sequential Compressed | Optimized | Full | High | Long tasks, production |

## Memory Management

### Short-term Memory
- Conversation buffer for immediate context
- Shared across agents in sequential patterns
- Isolated per agent in parallel patterns

### Long-term Memory
- Vector store with FAISS for semantic search
- Persistent storage with ChromaDB
- Automatic compression and retrieval

## Development

### Project Structure
```
src/multi_agent_task_breakdown/
├── __init__.py              # Main package exports
├── config.py               # AWS Bedrock and memory configuration
├── state.py                # AgentState TypedDict
├── orchestrator.py         # Main orchestrator class
├── agents/
│   ├── base_nodes.py       # Core agent nodes
│   └── compression_nodes.py # Compression-specific nodes
├── patterns/
│   ├── __init__.py         # Pattern exports
│   ├── parallel_unreliable.py
│   ├── parallel_shared.py
│   ├── sequential_reliable.py
│   └── sequential_compressed.py
└── cli.py                  # Command-line interface
```

### Adding New Patterns

1. Create a new pattern file in `patterns/`
2. Implement the graph creation function
3. Add to the pattern map in `orchestrator.py`
4. Update the `PatternType` literal

### Testing

```bash
# Run tests (when implemented)
uv run pytest

# Code formatting
uv run black src/
uv run isort src/

# Type checking
uv run mypy src/
```

## Production Deployment

### Recommended Pattern
Use **Pattern 3 (Sequential Reliable)** for most applications, upgrading to **Pattern 4 (Sequential Compressed)** when dealing with:
- Long-running tasks (>10 steps)
- Complex multi-turn conversations
- Memory-intensive workflows
- Production deployments requiring cost optimization

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
