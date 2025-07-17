# Basic Usage Guide

## 🎯 Purpose

This document provides a practical getting started guide for the Multi-Agent Task Breakdown system, with step-by-step instructions and examples.

## 🚀 Quick Start

### Installation and Setup

```
SETUP PROCESS

┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENVIRONMENT SETUP                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Step 1: Install uv (Python Package Manager)                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ curl -LsSf https://astral.sh/uv/install.sh | sh                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Step 2: Clone and Setup Project                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ git clone <repository-url>                                              │ │
│ │ cd multi-agent-task-breakdown                                           │ │
│ │ uv sync                                                                 │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Step 3: Configure AWS Credentials                                           │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ # Set up AWS credentials for Bedrock access                            │ │
│ │ aws configure                                                           │ │
│ │ # or set environment variables:                                         │ │
│ │ export AWS_ACCESS_KEY_ID=your_key                                       │ │
│ │ export AWS_SECRET_ACCESS_KEY=your_secret                                │ │
│ │ export AWS_DEFAULT_REGION=us-east-1                                     │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Step 4: Test Installation                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ uv run python examples/basic_usage.py                                   │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Your First Multi-Agent Task

```
HELLO WORLD EXAMPLE

Task: "Create a simple marketing plan for a new coffee shop"

┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1. USER INPUT                                                               │
│    ┌─────────────────────────────────────────────────────────────────────┐ │
│    │ "Create a marketing plan for Joe's Coffee - a new local coffee      │ │
│    │  shop in downtown Seattle targeting young professionals"            │ │
│    └─────────────────────────────────────────────────────────────────────┘ │
│                                     │                                       │
│                                     ▼                                       │
│ 2. TASK PLANNING                                                            │
│    ┌─────────────────────────────────────────────────────────────────────┐ │
│    │ System breaks down task into subtasks:                              │ │
│    │ ├── Analyze target market and competition                           │ │
│    │ ├── Define customer personas and segments                           │ │
│    │ ├── Develop key messaging and value proposition                     │ │
│    │ └── Create marketing campaign strategy                              │ │
│    └─────────────────────────────────────────────────────────────────────┘ │
│                                     │                                       │
│                                     ▼                                       │
│ 3. AGENT EXECUTION (Sequential)                                             │
│    ┌─────────────────────────────────────────────────────────────────────┐ │
│    │ Agent A: Market Analysis                                            │ │
│    │ → Researches Seattle coffee market, competitors, trends             │ │
│    │                                                                     │ │
│    │ Agent B: Customer Personas (uses market data)                      │ │
│    │ → Defines young professional segments, preferences                  │ │
│    │                                                                     │ │
│    │ Agent C: Messaging (uses market + personas)                        │ │
│    │ → Creates value props: quality, convenience, community              │ │
│    │                                                                     │ │
│    │ Agent D: Campaign Strategy (uses all previous work)                │ │
│    │ → Plans social media, local partnerships, grand opening            │ │
│    └─────────────────────────────────────────────────────────────────────┘ │
│                                     │                                       │
│                                     ▼                                       │
│ 4. RESULT AGGREGATION                                                       │
│    ┌─────────────────────────────────────────────────────────────────────┐ │
│    │ Complete marketing plan with:                                       │ │
│    │ ├── Market analysis and competitive landscape                       │ │
│    │ ├── Detailed customer personas and targeting                        │ │
│    │ ├── Compelling messaging and positioning                            │ │
│    │ └── Comprehensive campaign strategy with tactics                    │ │
│    └─────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔧 Running Examples

### Basic Example (Recommended Starting Point)

```python
# examples/basic_usage.py - Your starting point

from langchain_aws import ChatBedrock
from examples.pattern3_sequential_reliable import create_sequential_reliable_graph

def main():
    # Simple task for testing
    task = "Create a content strategy for a tech startup's blog"
    
    # Create the agent coordination graph
    graph = create_sequential_reliable_graph()
    
    # Run the task
    result = graph.invoke({
        "task": task,
        "messages": [],
        "subtasks": [],
        "sub_results": {},
        "final_result": "",
        "context": "",
        "step": "start"
    })
    
    print("="*60)
    print("MULTI-AGENT TASK BREAKDOWN RESULT")
    print("="*60)
    print(f"Task: {task}")
    print(f"Final Result: {result['final_result']}")
    print("="*60)

if __name__ == "__main__":
    main()
```

### Running Different Patterns

```
PATTERN COMPARISON COMMANDS

# Pattern 1: Parallel Unreliable (Educational - shows problems)
uv run python examples/pattern1_parallel_unreliable.py

# Pattern 2: Parallel with Shared Context (Use with caution)
uv run python examples/pattern2_parallel_shared.py

# Pattern 3: Sequential Reliable (RECOMMENDED for learning)
uv run python examples/pattern3_sequential_reliable.py

# Pattern 4: Sequential with Compression (Production ready)
uv run python examples/pattern4_sequential_compressed.py

# Enhanced with Memory (Advanced features)
uv run python examples/pattern3_sequential_reliable_enhanced.py

# Compare all patterns side-by-side
uv run python examples/compare_all_patterns.py
```

## 📊 Understanding the Output

### Example Output Structure

```
TYPICAL OUTPUT STRUCTURE

┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXECUTION RESULTS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ TASK: "Create marketing strategy for B2B mobile app"                        │
│                                                                             │
│ SUBTASKS COMPLETED:                                                         │
│ ├── analyze_market_conditions                                               │
│ │   └── "Market analysis: $50B TAM, 15% growth, enterprise-dominated..."   │
│ │                                                                           │
│ ├── identify_target_audience                                                │
│ │   └── "Primary: CTOs and VPs Engineering at Series A-C companies..."     │
│ │                                                                           │
│ ├── develop_key_messaging                                                   │
│ │   └── "Value props: 10x dev speed, 50% cost reduction, integration..."   │
│ │                                                                           │
│ └── create_campaign_plan                                                    │
│     └── "Multi-channel strategy: LinkedIn ads, dev conferences..."          │
│                                                                             │
│ FINAL RESULT:                                                               │
│ "Comprehensive B2B marketing strategy targeting CTOs and VPs of            │
│  Engineering with focus on development speed and cost benefits.            │
│  Campaign includes LinkedIn advertising, developer conference               │
│  presence, and thought leadership content, aligned with Q4/Q1              │
│  budget cycles and enterprise sales processes."                            │
│                                                                             │
│ EXECUTION METRICS:                                                          │
│ ├── Pattern Used: Sequential Reliable                                       │
│ ├── Total Time: 58.3 seconds                                               │
│ ├── Agents Used: 4                                                         │
│ └── Quality Score: 94/100                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Reading the Logs

```
LOG STRUCTURE EXPLANATION

[2024-01-15 10:30:00] INFO: Starting task planning
├── Task: "Create marketing strategy..."
├── Pattern: Sequential Reliable
└── Estimated agents: 4

[2024-01-15 10:30:05] INFO: Task planning complete
├── Subtasks identified: 4
├── Dependencies mapped: Yes
└── Execution order determined

[2024-01-15 10:30:05] INFO: Starting Agent A - Market Analysis
├── Input context: "Starting with market analysis"
├── Previous results: None (first agent)
└── Processing...

[2024-01-15 10:30:20] INFO: Agent A completed successfully
├── Output: "Comprehensive market analysis..."
├── Context updated: "Market analysis complete..."
└── Next agent: B (Target Audience)

[2024-01-15 10:30:20] INFO: Starting Agent B - Target Audience
├── Input context: "Market analysis complete. TAM $50B..."
├── Previous results: {"analyze_market": "..."}
└── Processing...

[2024-01-15 10:30:35] INFO: Agent B completed successfully
├── Output: "Primary: CTOs and VPs Engineering..."
├── Context updated: "Market + audience analysis complete..."
└── Next agent: C (Messaging)

[Continue for all agents...]

[2024-01-15 10:31:03] INFO: All agents completed successfully
├── Final aggregation starting
└── Quality validation: Passed

[2024-01-15 10:31:08] INFO: Task completed
├── Total execution time: 58.3s
├── Final result generated: Yes
└── Success: True
```

## ⚙️ Configuration Options

### Basic Configuration

```python
# Configuration options for basic usage

CONFIG = {
    # LLM Settings
    "llm_model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "max_tokens": 4096,
    "temperature": 0.1,
    
    # Pattern Selection
    "coordination_pattern": "sequential_reliable",  # Recommended
    # Options: parallel_unreliable, parallel_shared, 
    #          sequential_reliable, sequential_compressed
    
    # Memory Settings
    "enable_episodic_memory": False,  # Start simple
    "enable_semantic_memory": False,  # Add later
    "context_window_size": 8000,
    
    # Validation Settings
    "validate_steps": True,
    "max_retries": 3,
    "require_all_subtasks": True,
    
    # Monitoring
    "log_level": "INFO",
    "track_metrics": True,
    "save_results": True
}
```

### Advanced Configuration

```python
# Advanced configuration for production use

ADVANCED_CONFIG = {
    # Enhanced Memory (Pattern 3/4 Enhanced)
    "episodic_memory": {
        "enabled": True,
        "max_episodes": 1000,
        "similarity_threshold": 0.8,
        "hot_processing": True
    },
    
    "semantic_memory": {
        "enabled": True,
        "background_consolidation": True,
        "knowledge_graph": True,
        "user_preferences": True
    },
    
    # Context Compression (Pattern 4)
    "compression": {
        "enabled": True,
        "algorithm": "extractive_summarization",
        "compression_ratio": 0.3,
        "preserve_facts": True
    },
    
    # Error Handling
    "error_handling": {
        "retry_failed_agents": True,
        "escalate_after_retries": True,
        "partial_results_acceptable": False
    },
    
    # Performance Optimization
    "optimization": {
        "parallel_embeddings": True,
        "cache_repeated_operations": True,
        "batch_llm_calls": False  # Sequential nature
    }
}
```

## 🎯 Common Use Cases

### 1. Content Creation

```
CONTENT CREATION WORKFLOW

Task: "Create a comprehensive blog post about AI in healthcare"

Agent Breakdown:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Agent A: Research & Fact-Finding                                            │
│ ├── Current AI healthcare applications                                      │
│ ├── Recent breakthrough studies                                             │
│ ├── Industry statistics and trends                                          │
│ └── Expert opinions and quotes                                              │
│                                                                             │
│ Agent B: Structure & Outline (uses research)                                │
│ ├── Logical flow and sections                                               │
│ ├── Key points to cover                                                     │
│ ├── Target audience considerations                                           │
│ └── SEO and readability factors                                             │
│                                                                             │
│ Agent C: Content Writing (uses research + structure)                        │
│ ├── Engaging introduction                                                   │
│ ├── Detailed section content                                                │
│ ├── Smooth transitions                                                      │
│ └── Compelling conclusion                                                   │
│                                                                             │
│ Agent D: Review & Enhancement (uses everything)                             │
│ ├── Fact-checking and accuracy                                              │
│ ├── Style and tone consistency                                              │
│ ├── SEO optimization                                                        │
│ └── Final polish and formatting                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Recommended Pattern: Sequential Reliable (Pattern 3)
Why: Each step builds on previous work, quality is critical
```

### 2. Business Planning

```
BUSINESS PLANNING WORKFLOW

Task: "Develop a go-to-market strategy for a new SaaS product"

Agent Breakdown:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Agent A: Market & Competitive Analysis                                      │
│ ├── Total addressable market size                                           │
│ ├── Competitive landscape mapping                                           │
│ ├── Market trends and opportunities                                         │
│ └── Regulatory and industry factors                                         │
│                                                                             │
│ Agent B: Customer Research (uses market analysis)                           │
│ ├── Ideal customer profiles                                                 │
│ ├── Customer pain points and needs                                          │
│ ├── Buying process and decision makers                                      │
│ └── Customer acquisition costs                                              │
│                                                                             │
│ Agent C: Product Positioning (uses market + customer data)                  │
│ ├── Value proposition development                                           │
│ ├── Differentiation strategy                                                │
│ ├── Pricing strategy framework                                              │
│ └── Product-market fit assessment                                           │
│                                                                             │
│ Agent D: Go-to-Market Strategy (uses all previous work)                     │
│ ├── Marketing channel selection                                             │
│ ├── Sales process and enablement                                            │
│ ├── Launch timeline and milestones                                          │
│ └── Success metrics and KPIs                                                │
└─────────────────────────────────────────────────────────────────────────────┘

Recommended Pattern: Sequential Compressed (Pattern 4)
Why: Complex task with many dependencies, needs optimization
```

### 3. Research & Analysis

```
RESEARCH & ANALYSIS WORKFLOW

Task: "Analyze the impact of remote work on tech company productivity"

Agent Breakdown:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Agent A: Literature Review                                                  │
│ ├── Academic studies on remote work                                         │
│ ├── Industry reports and surveys                                            │
│ ├── Historical data and trends                                              │
│ └── Methodology assessment                                                  │
│                                                                             │
│ Agent B: Data Collection & Analysis (uses literature context)               │
│ ├── Productivity metrics identification                                     │
│ ├── Company case studies                                                    │
│ ├── Survey data and statistics                                              │
│ └── Quantitative analysis                                                   │
│                                                                             │
│ Agent C: Qualitative Analysis (uses data + literature)                      │
│ ├── Employee sentiment analysis                                             │
│ ├── Management perspectives                                                 │
│ ├── Cultural and team dynamics                                              │
│ └── Challenges and opportunities                                            │
│                                                                             │
│ Agent D: Synthesis & Conclusions (uses all analysis)                        │
│ ├── Key findings and insights                                               │
│ ├── Recommendations and best practices                                      │
│ ├── Future trends prediction                                                │
│ └── Executive summary                                                       │
└─────────────────────────────────────────────────────────────────────────────┘

Recommended Pattern: Sequential Reliable (Pattern 3)
Why: Research requires methodical approach, accuracy is critical
```

## 🔍 Troubleshooting Common Issues

### Problem: Agents Not Coordinating Properly

```
SYMPTOM: Inconsistent or contradictory results

DIAGNOSIS STEPS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Check Pattern Selection                                                  │
│    ├── Are you using Pattern 1 (Parallel Unreliable)?                     │
│    └── If yes: Switch to Pattern 3 (Sequential Reliable)                  │
│                                                                             │
│ 2. Verify Context Passing                                                  │
│    ├── Check logs for context updates between agents                      │
│    ├── Ensure state.context is being populated                            │
│    └── Verify sub_results are accessible to later agents                  │
│                                                                             │
│ 3. Review Agent Dependencies                                               │
│    ├── Map out what each agent needs from previous agents                 │
│    ├── Ensure logical ordering of subtasks                                │
│    └── Check for circular dependencies                                     │
└─────────────────────────────────────────────────────────────────────────────┘

SOLUTION:
# Use Pattern 3 with explicit context validation
def validate_context_flow(state):
    if state.step == "audience_analysis" and not state.sub_results.get("analyze_market"):
        raise ValueError("Market analysis required before audience analysis")
    return True
```

### Problem: Poor Quality Results

```
SYMPTOM: Generic or low-quality outputs

DIAGNOSIS STEPS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Check Task Specificity                                                  │
│    ├── Is your task description detailed enough?                           │
│    ├── Add context: industry, target audience, constraints                 │
│    └── Include examples of desired output quality                          │
│                                                                             │
│ 2. Review Agent Prompts                                                    │
│    ├── Are prompts specific to each agent's role?                         │
│    ├── Do prompts include context from previous agents?                   │
│    └── Are you asking for specific formats/details?                       │
│                                                                             │
│ 3. Enable Quality Validation                                               │
│    ├── Add output validation for each agent                               │
│    ├── Implement retry logic for poor results                             │
│    └── Use enhanced patterns with memory for learning                     │
└─────────────────────────────────────────────────────────────────────────────┘

SOLUTION:
# Enhanced task description
task = """
Create a comprehensive marketing strategy for a B2B mobile app that helps 
development teams track project progress. Target audience is CTOs and VPs 
of Engineering at Series A-C startups (50-500 employees). Focus on pain 
points around visibility, team coordination, and delivery predictability.
Include specific tactics, budget estimates, and success metrics.
"""
```

### Problem: Slow Execution

```
SYMPTOM: Tasks taking too long to complete

DIAGNOSIS STEPS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Pattern Analysis                                                         │
│    ├── Pattern 3 is inherently slower (sequential)                        │
│    ├── Consider Pattern 4 for large tasks (compression)                   │
│    └── Only use Pattern 2 if independence can be guaranteed               │
│                                                                             │
│ 2. Context Size Check                                                      │
│    ├── Monitor context growth between agents                              │
│    ├── Large contexts slow down LLM processing                            │
│    └── Enable compression for long tasks                                  │
│                                                                             │
│ 3. LLM Configuration                                                       │
│    ├── Check max_tokens setting (4096 recommended)                        │
│    ├── Verify AWS region (us-east-1 typically fastest)                   │
│    └── Monitor for rate limiting                                          │
└─────────────────────────────────────────────────────────────────────────────┘

SOLUTION:
# Use Pattern 4 with compression for large tasks
if len(subtasks) > 4:
    graph = create_sequential_compressed_graph()
else:
    graph = create_sequential_reliable_graph()
```

## 📈 Next Steps

### Level 1: Master the Basics
1. Run all basic examples successfully
2. Create your own simple 3-4 agent tasks
3. Understand Pattern 3 (Sequential Reliable) thoroughly
4. Practice reading and interpreting results

### Level 2: Production Readiness
1. Implement Pattern 4 (Sequential Compressed)
2. Add proper error handling and validation
3. Set up monitoring and logging
4. Create custom task templates for your use cases

### Level 3: Advanced Features
1. Enable enhanced memory management
2. Implement episodic and semantic memory
3. Add background processing and learning
4. Create domain-specific agent specializations

### Level 4: Custom Patterns
1. Design custom coordination patterns
2. Implement specialized memory architectures
3. Add advanced monitoring and analytics
4. Contribute back to the project

## 🔗 Related Documentation

- [Pattern Comparison](./10_pattern_comparison.md) - Choose the right pattern
- [Pattern 3: Sequential Reliable](./06_pattern3_sequential_reliable.md) - Recommended starting point
- [Enhanced Memory Management](./08_enhanced_memory.md) - Advanced features
- [Running Examples](./12_running_examples.md) - Detailed execution guide