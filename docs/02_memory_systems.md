# Memory Systems

## 🎯 Purpose

This document explains the advanced memory architecture that enables the system to learn from past interactions, store world knowledge, and provide personalized responses based on the CoALA (Cognitive Architecture for Language Agents) framework.

## 🔧 Memory Architecture Overview

### Dual Memory System

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                              Memory Architecture                                │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐      │
│  │         EPISODIC MEMORY         │  │         SEMANTIC MEMORY         │      │
│  │    (Experience-Based)           │  │      (Knowledge-Based)          │      │
│  │                                 │  │                                 │      │
│  │  ┌─────────────────────────────┐ │  │  ┌─────────────────────────────┐ │      │
│  │  │  • Specific Interactions    │ │  │  │  • World Knowledge          │ │      │
│  │  │  • Action Sequences         │ │  │  │  • User Preferences         │ │      │
│  │  │  • Successful Patterns      │ │  │  │  • Abstract Concepts        │ │      │
│  │  │  • Temporal Context         │ │  │  │  • Factual Information      │ │      │
│  │  │  • Episode Metadata         │ │  │  │  • Relationship Patterns    │ │      │
│  │  └─────────────────────────────┘ │  │  └─────────────────────────────┘ │      │
│  │                │                 │  │                │                 │      │
│  │                ▼                 │  │                ▼                 │      │
│  │  ┌─────────────────────────────┐ │  │  ┌─────────────────────────────┐ │      │
│  │  │      HOT PROCESSING         │ │  │  │   BACKGROUND CONSOLIDATION  │ │      │
│  │  │ • Real-time updates         │ │  │  │ • Knowledge graph building  │ │      │
│  │  │ • Pattern recognition       │ │  │  │ • Fact extraction           │ │      │
│  │  │ • Success tracking          │ │  │  │ • Preference learning       │ │      │
│  │  │ • Context enrichment        │ │  │  │ • Concept abstraction       │ │      │
│  │  └─────────────────────────────┘ │  │  └─────────────────────────────┘ │      │
│  └─────────────────────────────────┘  └─────────────────────────────────┘      │
│                        │                              │                        │
│                        └──────────────┬───────────────┘                        │
│                                       ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         RETRIEVAL & INTEGRATION                             │ │
│  │                                                                             │ │
│  │  Similarity Search  ──▶  Context Assembly  ──▶  Personalized Responses     │ │
│  │  Temporal Queries   ──▶  Knowledge Fusion  ──▶  Learning Applications      │ │
│  │  Pattern Matching   ──▶  Memory Synthesis  ──▶  Adaptive Behavior          │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

## 📊 Episodic Memory System

### Episode Structure and Storage

```
┌─────────────────────────────────────────────────────────────────┐
│                      EPISODIC MEMORY                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EPISODE CREATION                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ User Action │─▶│ Agent Steps │─▶│ Outcome     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         │                 │                 │                  │
│         ▼                 ▼                 ▼                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Episode Record                           │ │
│  │                                                             │ │
│  │  {                                                          │ │
│  │    "id": "uuid-string",                                     │ │
│  │    "timestamp": "2024-01-15T10:30:00Z",                    │ │
│  │    "user_input": "Create marketing strategy",               │ │
│  │    "actions": [                                            │ │
│  │      "analyze_market",                                      │ │
│  │      "identify_target_audience",                           │ │
│  │      "develop_messaging",                                  │ │
│  │      "create_campaign_plan"                                │ │
│  │    ],                                                       │ │
│  │    "outcome": "Comprehensive strategy delivered",           │ │
│  │    "success": true,                                         │ │
│  │    "duration": 45.3,                                       │ │
│  │    "context": "mobile app marketing",                      │ │
│  │    "metadata": {                                           │ │
│  │      "user_satisfaction": 9.2,                             │ │
│  │      "pattern_type": "sequential_reliable",                │ │
│  │      "complexity": "high"                                  │ │
│  │    }                                                        │ │
│  │  }                                                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                 │                               │
│                                 ▼                               │
│  STORAGE & INDEXING                                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Vector Embeddings                        │ │
│  │                                                             │ │
│  │  Episode Text ──▶ Titan Embeddings ──▶ FAISS Index         │ │
│  │       │                   │                   │             │ │
│  │       ▼                   ▼                   ▼             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │ │
│  │  │ Searchable  │  │ Similarity  │  │ Fast        │         │ │
│  │  │ Content     │  │ Matching    │  │ Retrieval   │         │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Episode Retrieval Process

```
Query: "How to create marketing strategy?"
   │
   ▼
┌─────────────────┐
│ Embed Query     │ ← Titan Embeddings
└─────────────────┘
   │
   ▼
┌─────────────────┐
│ FAISS Search    │ ← Similarity search in episode vectors
└─────────────────┘
   │
   ▼
┌─────────────────┐
│ Rank Episodes   │ ← By relevance, recency, success rate
└─────────────────┘
   │
   ▼
┌─────────────────┐
│ Extract Patterns│ ← Successful action sequences
└─────────────────┘
   │
   ▼
┌─────────────────┐
│ Context Build   │ ← Prepare for current task
└─────────────────┘

Retrieved Episodes:
├── Episode #1247 (similarity: 0.94)
│   └── Actions: analyze_market → identify_audience → develop_messaging
├── Episode #1201 (similarity: 0.87)
│   └── Actions: research_competitors → define_value_prop → create_campaign
└── Episode #1156 (similarity: 0.82)
    └── Actions: user_research → persona_development → channel_strategy
```

## 🧠 Semantic Memory System

### Knowledge Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SEMANTIC MEMORY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KNOWLEDGE CATEGORIES                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ WORLD KNOWLEDGE │  │ USER PREFERENCES│  │  RELATIONSHIPS  │             │
│  │                 │  │                 │  │                 │             │
│  │ • Domain Facts  │  │ • Style Prefs   │  │ • Concept Links │             │
│  │ • Procedures    │  │ • Tool Choices  │  │ • Cause-Effect  │             │
│  │ • Best Practices│  │ • Communication │  │ • Hierarchies   │             │
│  │ • Industry Info │  │ • Work Patterns │  │ • Dependencies  │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│         │                       │                       │                  │
│         └───────────────────────┼───────────────────────┘                  │
│                                 ▼                                          │
│  KNOWLEDGE GRAPH                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                         │ │
│  │   [Marketing Strategy] ──── requires ───▶ [Market Analysis]             │ │
│  │           │                                       │                     │ │
│  │           ├─── includes ───▶ [Target Audience]    │                     │ │
│  │           │                         │             │                     │ │
│  │           ├─── uses ──────▶ [Messaging]           │                     │ │
│  │           │                         │             │                     │ │
│  │           └─── outputs ───▶ [Campaign Plan] ◀─────┘                     │ │
│  │                                     │                                   │ │
│  │   [User: John] ─── prefers ───▶ [Sequential Pattern]                    │ │
│  │           │                                                             │ │
│  │           ├─── likes ──────▶ [Detailed Analysis]                        │ │
│  │           │                                                             │ │
│  │           └─── avoids ─────▶ [Parallel Execution]                       │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Background Consolidation Process

```
BACKGROUND CONSOLIDATION PIPELINE

Step 1: Episode Analysis
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ New Episodes    │───▶│ Pattern Extract │───▶│ Fact Identify   │
│ (from hotmem)   │    │ (ML Analysis)   │    │ (NLP Extract)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
Step 2: Knowledge Integration
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Existing Graph  │◀───│ Graph Update    │◀───│ New Knowledge   │
│ (semantic mem)  │    │ (Add/Modify)    │    │ (validated)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
Step 3: Preference Learning
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ User Behavior   │───▶│ Pattern Learn   │───▶│ Preference      │
│ (success data)  │    │ (clustering)    │    │ Update          │
└─────────────────┘    └─────────────────┘    └─────────────────┘

Examples of Extracted Knowledge:

FACTS:
• "Marketing strategies require market analysis as first step"
• "Target audience identification improves campaign success by 40%"
• "Sequential execution pattern works best for complex strategies"

PREFERENCES:
• User prefers detailed step-by-step breakdowns
• User responds well to data-driven insights
• User typically works on B2B technology products

RELATIONSHIPS:
• Market Analysis → Target Audience → Messaging → Campaign
• User satisfaction correlates with execution time < 60 seconds
• Sequential pattern success rate: 94% vs Parallel: 67%
```

## 🔄 Memory Integration and Context Assembly

### Context Window Optimization

```
CONTEXT ASSEMBLY PROCESS

Input: User Task + Query
   │
   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MEMORY RETRIEVAL                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  EPISODIC RETRIEVAL           SEMANTIC RETRIEVAL                            │
│  ┌─────────────────┐          ┌─────────────────┐                          │
│  │ Similar Tasks   │          │ Relevant Facts  │                          │
│  │ • 3 episodes    │          │ • Domain know.  │                          │
│  │ • Success rate  │          │ • Best practices│                          │
│  │ • Action seq.   │          │ • User prefs    │                          │
│  └─────────────────┘          └─────────────────┘                          │
│         │                              │                                   │
│         └──────────────┬───────────────┘                                   │
│                        ▼                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                   CONTEXT SYNTHESIS                                     │ │
│  │                                                                         │ │
│  │  Priority Ranking:                                                      │ │
│  │  1. Recent successful episodes (weight: 0.4)                           │ │
│  │  2. User preferences (weight: 0.3)                                     │ │
│  │  3. Domain knowledge (weight: 0.2)                                     │ │
│  │  4. General best practices (weight: 0.1)                               │ │
│  │                                                                         │ │
│  │  Context Assembly:                                                      │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │ │
│  │  │ Episode     │+│ Preferences │+│ Facts       │+│ Patterns    │       │ │
│  │  │ Patterns    │ │ (Personal)  │ │ (Domain)    │ │ (General)   │       │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │ │
│  │         │               │               │               │               │ │
│  │         └───────────────┼───────────────┼───────────────┘               │ │
│  │                         ▼               ▼                               │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐ │ │
│  │  │                   OPTIMIZED CONTEXT                                 │ │ │
│  │  │                                                                     │ │ │
│  │  │  "Based on your previous successful marketing strategies:           │ │ │
│  │  │   • Always start with market analysis (98% success rate)           │ │ │
│  │  │   • You prefer sequential execution for complex tasks               │ │ │
│  │  │   • Focus on B2B tech audience (your usual domain)                 │ │ │
│  │  │   • Include data-driven insights (increases satisfaction)           │ │ │
│  │  │   • Use 4-step process: analyze → target → message → plan"         │ │ │
│  │  └─────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────────────┐
                          │    PERSONALIZED EXECUTION       │
                          │    (with memory-enhanced        │
                          │     context)                    │
                          └─────────────────────────────────┘
```

## ⚡ Key Features

### 1. Hot vs. Background Processing

```
HOT PROCESSING (Real-time)          BACKGROUND PROCESSING (Async)
┌─────────────────────────────┐     ┌─────────────────────────────┐
│ • Episode storage           │     │ • Knowledge graph updates   │
│ • Immediate pattern match   │     │ • Preference learning       │
│ • Context enrichment        │     │ • Fact extraction           │
│ • Quick retrieval           │     │ • Relationship discovery    │
│ • Session continuity        │     │ • Performance optimization  │
└─────────────────────────────┘     └─────────────────────────────┘
            │                                   │
            ▼                                   ▼
    During execution                    Between sessions
    (<100ms response)                   (minutes/hours)
```

### 2. Memory Persistence Layers

```
MEMORY PERSISTENCE ARCHITECTURE

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Session Memory  │    │ FAISS Vectors   │    │ ChromaDB        │
│ (RAM)          │───▶│ (In-Memory)     │───▶│ (Persistent)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
       │                       │                       │
       ▼                       ▼                       ▼
• Active context        • Fast similarity        • Cross-session
• Working memory        • Real-time search       • Long-term storage
• Current episode       • Hot processing         • Backup & recovery
• Immediate access      • Memory optimization    • Distributed scaling

Lifecycle:
New Episode ──▶ Session ──▶ FAISS ──▶ ChromaDB ──▶ Analytics
   (0ms)       (session)   (<100ms)    (async)      (batch)
```

## ⚠️ Trade-offs

### Memory vs. Performance

```
High Memory Detail    ←──────────────────────→    High Performance
        │                                              │
    Full Episode           Compressed           Summarized
    Preservation           Memories             Patterns
        │                      │                      │
• Complete context      • Balanced detail      • Key patterns only
• Highest accuracy     • Good performance     • Fastest retrieval
• Slower retrieval     • Moderate memory      • Lowest memory
• High storage cost    • Reasonable cost      • Minimal cost
```

### Learning vs. Privacy

```
High Learning Capability ←──────────────────→ High Privacy Protection
        │                                              │
   Deep Personal         Balanced Learning      Minimal Learning
   Profiling            with Privacy           Anonymous Only
        │                      │                      │
• Detailed preferences  • Selective storage    • Pattern-only
• Personal patterns     • Data filtering       • No personal data
• Custom behavior       • Anonymization       • Generic responses
• Privacy concerns      • Moderate learning    • No customization
```

## 💡 Use Cases

### Memory Configuration by Use Case

| Use Case | Episodic Memory | Semantic Memory | Background Processing | Persistence |
|----------|----------------|-----------------|----------------------|-------------|
| **Personal Assistant** | Full episodes | Deep user prefs | Continuous | Full persistence |
| **Enterprise Tool** | Work patterns | Domain knowledge | Scheduled | Filtered persistence |
| **Research System** | Method tracking | World knowledge | Intensive | Full persistence |
| **Privacy-First** | Minimal episodes | Anonymous facts | Limited | Session only |

### Memory Benefits

1. **Personalization**: Adapts to user preferences and working styles
2. **Learning**: Improves performance based on successful patterns
3. **Efficiency**: Reduces redundant work by reusing proven approaches
4. **Context**: Maintains conversation continuity across sessions
5. **Intelligence**: Builds domain expertise over time

## 🔗 Related Documentation

- [Architecture Overview](./01_architecture_overview.md) - Overall system design
- [State Management](./03_state_management.md) - LangGraph state handling
- [Enhanced Memory Management](./08_enhanced_memory.md) - Implementation details
- [Memory Persistence](./09_memory_persistence.md) - Cross-session storage