# 🚀 Tech Radar Agent

A deep research agent that generates Technology Radars by evaluating technologies through systematic research, metric collection, and heuristic-based decision-making.

## 🚀 Quickstart

**Prerequisites**: Install [uv](https://docs.astral.sh/uv/) package manager:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Ensure you are in the `deep_research` directory:
```bash
cd deep_research
```

Install packages:
```bash
uv sync
```

Set your API keys in your environment:

```bash
export ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Required for Claude model
export GOOGLE_API_KEY=your_google_api_key_here        # Required for Gemini model ([get one here](https://ai.google.dev/gemini-api/docs))
export TAVILY_API_KEY=your_tavily_api_key_here        # Required for web search ([get one here](https://www.tavily.com/)) with a generous free tier
export LANGSMITH_API_KEY=your_langsmith_api_key_here  # [LangSmith API key](https://smith.langchain.com/settings) (free to sign up)
```

## What is a Tech Radar?

A Technology Radar is a strategic tool for assessing and visualizing the maturity and adoption readiness of technologies, platforms, tools, and techniques. Technologies are placed in one of four rings based on data-driven evaluation:

- **Adopt**: Proven, stable, recommended for production use
- **Trial**: Ready for testing in production-like environments
- **Assess**: Worth exploring with small experiments
- **Hold**: Avoid or proceed with extreme caution

## Usage Options

You can run this quickstart in two ways:

### Option 1: Jupyter Notebook

Run the interactive notebook to step through the Tech Radar generation process:

```bash
uv run jupyter notebook research_agent.ipynb
```

### Option 2: LangGraph Server

Run a local [LangGraph server](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/) with a web interface:

```bash
langgraph dev
```

LangGraph server will open a new browser window with the Studio interface where you can request Tech Radar generation: 

<img width="2869" height="1512" alt="Screenshot 2025-11-17 at 11 42 59 AM" src="https://github.com/user-attachments/assets/03090057-c199-42fe-a0f7-769704c2124b" />

You can also connect the LangGraph server to a [UI specifically designed for deepagents](https://github.com/langchain-ai/deep-agents-ui):

```bash
$ git clone https://github.com/langchain-ai/deep-agents-ui.git
$ cd deep-agents-ui
$ yarn install
$ yarn dev
```

- **[Tech Radar Methodology](https://www.thoughtworks.com/radar/byor)** - Original Tech Radar approach by ThoughtWorks

## Architecture

### Workflow

The agent follows a structured 7-step workflow:

1. **Decompose Scope** - Identify technologies and group into radar quadrants
2. **Delegate Metric Research** - Sub-agents collect objective metrics per technology
3. **Normalize & Profile** - Create consistent technology profiles
4. **Evaluate Trends & Risks** - Assess momentum and operational risks
5. **Make Ring Decisions** - Apply explicit heuristics for placement
6. **Validate Consistency** - Check radar structural integrity
7. **Export Results** - Generate markdown output

### Tool Categories

**Research Tools**:
- `tavily_search` - Web search for technology information
- `think_tool` - Strategic reflection and decision-making

**Data Acquisition Tools**:
- `gTech Radar agent uses custom instructions defined in `deep_research/research_agent/prompts.py` that guide structured technology evaluation. You can modify these to fit your organization's needs.

| Instruction Set | Purpose |
|----------------|---------|
| `TECH_RADAR_WORKFLOW_INSTRUCTIONS` | Defines the 7-step Tech Radar generation workflow: decompose scope → delegate metric research → normalize & profile → evaluate trends & risks → make ring decisions → validate consistency → export radar. Enforces data-driven decision-making with explicit rules against intuition-based placements. |
| `SUBAGENT_DELEGATION_INSTRUCTIONS` | Provides delegation strategies: bias towards single comprehensive research (most queries), parallelize only for explicit comparisons (1 sub-agent per technology when comparing). Sets limits on parallel execution (max 3 concurrent) and iteration rounds (max 3). |
| `RADAR_RESEARCHER_INSTRUCTIONS` | Guides research sub-agents to extract objective metrics only (GitHub stats, release patterns, security signals, adoption mentions). Explicitly forbids ring assignments or recommendations - only data collection. Requires structured output with citations
- `technology_profile_tool` - Normalize metrics into profiles
- `tech_trend_tool` - Momentum and volatility assessment
- `compare_technologies_tool` - Relative comparisons within quadrants
- `rTech Radar agent uses 18 specialized tools organized into three categories. You can also add your own tools, including via MCP servers. See the Deepagents package [README](https://github.com/langchain-ai/deepagents?tab=readme-ov-file#mcp) for more details.

#### Research Tools

| Tool Name | Description |
|-----------|-------------|
| `tavily_search` | Web search tool that discovers URLs via Tavily API, fetches full webpage content via HTTP with proper User-Agent headers, converts HTML to markdown, and returns complete content for agent analysis. |
| `think_tool` | Strategic reflection mechanism for pausing between searches to assess progress, analyze findings, identify gaps, and plan next steps. |

#### Data Acquisition Tools

| Tool Name | Description |
|-----------|-------------|
| `github_repo_metrics_tool` | Fetches GitHub repository metrics using public REST API (no auth): stars, monthly commits, monthly releases, contributors, first release year. Subject to 60 req/hour unauthenticated rate limit. |
| `github_release_analysis_tool` | Analyzes GitHub releases for breaking changes using semantic versioning heuristics (major version bumps indicate breaking changes). |
| `security_incidents_tool` | Checks GitHub security advisories for vulnerability signals. Unauthenticated access may miss private advisories. |
| `enterprise_adoption_tool` | Estimates enterprise adoption via Tavily search for case studies and enterprise usage mentions. |
| `pricing_volatility_tool` | Detects pricing changes by analyzing vendor pricing pages for keywords like "increase", "changed pricing", "deprecated". |

#### Evaluation & Decision Tools

| Tool Name | Description |
|-----------|-------------|
| `technology_profile_tool` | Normalizes raw metrics into consistent profiles with calculated maturity scores based on age, stars, contributors, and enterprise mentions. |
| `tech_trend_tool` | Analyzes momentum (increasing/stable/declining) and volatility from commit activity, releases, and breaking changes using heuristic thresholds. |
| `compare_technologies_tool` | Performs relative comparison of technologies within the same quadrant based on normalized adoption and activity scores. |
| `risk_assessment_tool` | Evaluates operational/strategic risk from security incidents, API instability, vendor lock-in, cost volatility, and safety concerns. Returns risk level and ring ceiling (maximum allowed ring). |
| `org_context_tool` | Applies organizational constraints (size, risk tolerance, compliance level) to adjust evaluation thresholds. |
| `ring_decision_tool` | Makes final ring placement using explicit heuristic rules combining maturity score, momentum, risk ceiling, and organizational constraints. Returns ring, confidence score, and justification. |
| `radar_consistency_tool` | Validates radar structure for anomalies (e.g., too many "Adopt" placements, no "Hold" items). |
| `radar_export_tool` | Exports Tech Radar to markdown format with quadrants, technologies, and ring assignments. |

### Decision Heuristics

Ring placement follows explicit, traceable rules:

```python
# Base score calculation
score = (maturity_score * 0.5) + (momentum_bonus * 0.3) - compliance_penalty

# Ring thresholds
if score >= 0.75: proposed = "Adopt"
elif score >= 0.5: proposed = "Trial"  
elif score >= 0.3: proposed = "Assess"
else: proposed = "Hold"

# Risk ceiling enforcement (caps maximum ring)
final_ring = min(proposed, risk_ceiling)
```

Every decision includes confidence scores and justifications traceable to source metrics.ct the UI to the running LangGraph server.

This provides a user-friendly chat interface and visualization of files in state. 

<img width="2039" height="1495" alt="Screenshot 2025-11-17 at 1 11 27 PM" src="https://github.com/user-attachments/assets/d559876b-4c90-46fb-8e70-c16c93793fa8" />

## 📚 Resources

- **[Deep Research Course](https://academy.langchain.com/courses/deep-research-with-langgraph)** - Full course on deep research with LangGraph

### Custom Model

By default, `deepagents` uses `"claude-sonnet-4-5-20250929"`. You can customize this by passing any [LangChain model object](https://python.langchain.com/docs/integrations/chat/). See the Deepagents package [README](https://github.com/langchain-ai/deepagents?tab=readme-ov-file#model) for more details.

```python
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

# Using Claude
model = init_chat_model(model="anthropic:claude-sonnet-4-5-20250929", temperature=0.0)

# Using Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
model = ChatGoogleGenerativeAI(model="gemini-3-pro-preview")

agent = create_deep_agent(
    model=model,
)
```

### Custom Instructions

The deep research agent uses custom instructions defined in `deep_research/research_agent/prompts.py` that complement (rather than duplicate) the default middleware instructions. You can modify these in any way you want. 

| Instruction Set | Purpose |
|----------------|---------|
| `RESEARCH_WORKFLOW_INSTRUCTIONS` | Defines the 5-step research workflow: save request → plan with TODOs → delegate to sub-agents → synthesize → respond. Includes research-specific planning guidelines like batching similar tasks and scaling rules for different query types. |
| `SUBAGENT_DELEGATION_INSTRUCTIONS` | Provides concrete delegation strategies with examples: simple queries use 1 sub-agent, comparisons use 1 per element, multi-faceted research uses 1 per aspect. Sets limits on parallel execution (max 3 concurrent) and iteration rounds (max 3). |
| `RESEARCHER_INSTRUCTIONS` | Guides individual research sub-agents to conduct focused web searches. Includes hard limits (2-3 searches for simple queries, max 5 for complex), emphasizes using `think_tool` after each search for strategic reflection, and defines stopping criteria. |

### Custom Tools

The deep research agent adds the following custom tools beyond the built-in deepagent tools. You can also use your own tools, including via MCP servers. See the Deepagents package [README](https://github.com/langchain-ai/deepagents?tab=readme-ov-file#mcp) for more details.

| Tool Name | Description |
|-----------|-------------|
| `tavily_search` | Web search tool that uses Tavily purely as a URL discovery engine. Performs searches using Tavily API to find relevant URLs, fetches full webpage content via HTTP with proper User-Agent headers (avoiding 403 errors), converts HTML to markdown, and returns the complete content without summarization to preserve all information for the agent's analysis. Works with both Claude and Gemini models. |
| `think_tool` | Strategic reflection mechanism that helps the agent pause and assess progress between searches, analyze findings, identify gaps, and plan next steps. |

