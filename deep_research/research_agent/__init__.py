"""Deep Research Agent Example.

This module demonstrates building a research agent using the deepagents package
with custom tools for web search and strategic thinking.
"""

from research_agent.prompts import (
    RADAR_RESEARCHER_INSTRUCTIONS,
    TECH_RADAR_WORKFLOW_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)
from research_agent.tools import tavily_search, think_tool

__all__ = [
    "tavily_search",
    "think_tool",
    "RADAR_RESEARCHER_INSTRUCTIONS",
    "TECH_RADAR_WORKFLOW_INSTRUCTIONS",
    "SUBAGENT_DELEGATION_INSTRUCTIONS",
]
