"""Tech Radar Agent - Standalone script for LangGraph deployment.

This module creates a deep agent capable of generating Technology Radars
by combining web research, metric extraction, heuristic evaluation,
and structured decision-making.
"""

from datetime import datetime

from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

from research_agent.prompts import (
    TECH_RADAR_WORKFLOW_INSTRUCTIONS,
    RADAR_RESEARCHER_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)

from research_agent.tools import (
    # Research
    tavily_search,
    think_tool,

    # Data acquisition
    github_repo_metrics_tool,
    github_release_analysis_tool,
    security_incidents_tool,
    enterprise_adoption_tool,
    pricing_volatility_tool,

    # Evaluation & decision
    technology_profile_tool,
    tech_trend_tool,
    risk_assessment_tool,
    org_context_tool,
    ring_decision_tool,
    generate_radar_tool,
    radar_consistency_tool,
    radar_export_tool,
)

# Limits
max_concurrent_research_units = 3
max_researcher_iterations = 3

current_date = datetime.now().strftime("%Y-%m-%d")

# System instructions for orchestrator
INSTRUCTIONS = (
    TECH_RADAR_WORKFLOW_INSTRUCTIONS
    + "\n\n"
    + "=" * 80
    + "\n\n"
    + SUBAGENT_DELEGATION_INSTRUCTIONS.format(
        max_concurrent_research_units=max_concurrent_research_units,
        max_researcher_iterations=max_researcher_iterations,
    )
)

# Tech Radar research sub-agent
research_sub_agent = {
    "name": "radar-researcher",
    "description": (
        "Research and extract objective metrics about a single technology "
        "for Tech Radar evaluation. Do NOT make ring decisions."
    ),
    "system_prompt": RADAR_RESEARCHER_INSTRUCTIONS.format(date=current_date),
    "tools": [
        tavily_search,
        think_tool,
    ],
}

# Model
model = init_chat_model(
    model="openai:gpt-4o",
    temperature=0.0,
)

# Create the deep agent
agent = create_deep_agent(
    model=model,
    tools=[
        # Research
        tavily_search,
        think_tool,

        # Data acquisition
        github_repo_metrics_tool,
        github_release_analysis_tool,
        security_incidents_tool,
        enterprise_adoption_tool,
        pricing_volatility_tool,

        # Evaluation & decision
        technology_profile_tool,
        tech_trend_tool,
        risk_assessment_tool,
        org_context_tool,
        ring_decision_tool,
        generate_radar_tool,
        radar_consistency_tool,
        radar_export_tool,
    ],
    system_prompt=INSTRUCTIONS,
    subagents=[research_sub_agent],
)
