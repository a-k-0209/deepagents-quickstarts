"""Research Tools.

This module provides search and content processing utilities for the research agent,
using Tavily for URL discovery and fetching full webpage content.

Tech Radar Tools.

This module also provides evaluation, governance, and export utilities for generating
Technology Radars in a principled, explainable manner. Tools are data-driven
(real metrics as inputs) and heuristic-interpreted (explicit decision rules).
"""

import httpx
import os
from datetime import datetime, timedelta
from langchain_core.tools import InjectedToolArg, tool
from markdownify import markdownify
from tavily import TavilyClient
from typing_extensions import Annotated, Literal, TypedDict
from typing import Dict, List, Literal
import statistics
import json


# ---------------------------------------------------------------------
# Typed Schemas
# ---------------------------------------------------------------------

class TechnologyMetrics(TypedDict):
    github_stars: int
    monthly_commits: int
    monthly_releases: int
    breaking_changes: bool
    contributors: int
    enterprise_mentions: int
    first_release_year: int


class RiskMetrics(TypedDict):
    security_incidents: int
    api_instability: bool
    vendor_lock_in: bool
    cost_volatility: bool
    safety_risk: bool


class OrgContext(TypedDict):
    org_size: Literal["startup", "mid", "enterprise"]
    risk_tolerance: Literal["low", "medium", "high"]
    domain: str
    compliance_level: Literal["low", "medium", "high"]

# ---------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------

tavily_client = TavilyClient()


def fetch_webpage_content(url: str, timeout: float = 10.0) -> str:
    """Fetch and convert webpage content to markdown.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Webpage content as markdown
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = httpx.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return markdownify(response.text)
    except Exception as e:
        return f"Error fetching content from {url}: {str(e)}"


@tool(parse_docstring=True)
def tavily_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 1,
    topic: Annotated[
        Literal["general", "news", "finance"], InjectedToolArg
    ] = "general",
) -> str:
    """Search the web for information on a given query.

    Uses Tavily to discover relevant URLs, then fetches and returns full webpage content as markdown.

    Args:
        query: Search query to execute
        max_results: Maximum number of results to return (default: 1)
        topic: Topic filter - 'general', 'news', or 'finance' (default: 'general')

    Returns:
        Formatted search results with full webpage content
    """
    # Use Tavily to discover URLs
    search_results = tavily_client.search(
        query,
        max_results=max_results,
        topic=topic,
    )

    # Fetch full content for each URL
    result_texts = []
    for result in search_results.get("results", []):
        url = result["url"]
        title = result["title"]

        # Fetch webpage content
        content = fetch_webpage_content(url)

        result_text = f"""## {title}
**URL:** {url}

{content}

---
"""
        result_texts.append(result_text)

    # Format final response
    response = f"""🔍 Found {len(result_texts)} result(s) for '{query}':

{chr(10).join(result_texts)}"""

    return response


@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection recorded: {reflection}"

@tool(parse_docstring=True)
def technology_profile_tool(
    name: str,
    category: str,
    metrics: TechnologyMetrics
) -> Dict:
    """
    Build a structured technology profile from externally collected metrics.

    This tool does NOT fetch data. It normalizes provided signals into a
    consistent profile used downstream for evaluation and comparison.

    Args:
        name: Name of the technology
        category: Radar quadrant (e.g., Agent Framework, Model, Platform)
        metrics: Observed external metrics for the technology

    Returns:
        Normalized technology profile with maturity indicators
    """
    age = max(1, 2026 - metrics["first_release_year"])
    maturity_score = min(
        1.0,
        (
            (metrics["github_stars"] / 5000)
            + (metrics["contributors"] / 100)
            + (metrics["enterprise_mentions"] / 10)
        ) / age
    )

    return {
        "name": name,
        "category": category,
        "age_years": age,
        "metrics": metrics,
        "maturity_score": round(maturity_score, 2),
    }


@tool(parse_docstring=True)
def tech_trend_tool(metrics: TechnologyMetrics) -> Dict:
    """
    Analyze momentum and volatility from time-based contribution metrics.

    Uses heuristic thresholds to interpret raw activity signals.

    Args:
        metrics: Observed activity metrics

    Returns:
        Trend and momentum assessment
    """
    momentum_score = (
        metrics["monthly_commits"] * 0.4
        + metrics["monthly_releases"] * 0.4
        + metrics["contributors"] * 0.2
    )

    volatility = "high" if metrics["breaking_changes"] else "low"

    if momentum_score > 50:
        momentum = "increasing"
    elif momentum_score > 20:
        momentum = "stable"
    else:
        momentum = "declining"

    return {
        "momentum": momentum,
        "volatility": volatility,
        "momentum_score": momentum_score,
    }

@tool(parse_docstring=True)
def risk_assessment_tool(risks: RiskMetrics) -> Dict:
    """
    Assess operational and strategic risk for a technology.

    Explicit rules cap promotion into higher radar rings.

    Args:
        risks: Observed risk indicators

    Returns:
        Risk level, key concerns, and maximum allowed ring
    """
    risk_score = (
        risks["security_incidents"] * 0.3
        + int(risks["api_instability"]) * 0.3
        + int(risks["vendor_lock_in"]) * 0.2
        + int(risks["cost_volatility"]) * 0.1
        + int(risks["safety_risk"]) * 0.3
    )

    if risk_score >= 1.0:
        max_ring = "Assess"
        level = "high"
    elif risk_score >= 0.5:
        max_ring = "Trial"
        level = "medium"
    else:
        max_ring = "Adopt"
        level = "low"

    return {
        "risk_level": level,
        "risk_score": round(risk_score, 2),
        "ring_ceiling": max_ring,
    }


@tool(parse_docstring=True)
def org_context_tool(context: OrgContext) -> Dict:
    """
    Normalize organizational constraints for radar interpretation.

    This tool is stateless and provides thresholds used by the agent.

    Args:
        context: Organization profile and constraints

    Returns:
        Interpretable organizational constraints
    """
    strictness = {
        "startup": 0.3,
        "mid": 0.6,
        "enterprise": 0.9,
    }[context["org_size"]]

    compliance_penalty = {
        "low": 0.0,
        "medium": 0.2,
        "high": 0.4,
    }[context["compliance_level"]]

    return {
        "strictness": strictness,
        "compliance_penalty": compliance_penalty,
        "risk_tolerance": context["risk_tolerance"],
        "domain": context["domain"],
    }


RING_ORDER = ["Hold", "Assess", "Trial", "Adopt"]

@tool(parse_docstring=True)
def ring_decision_tool(
    maturity_score: float,
    trend: Dict,
    risk: Dict,
    org_constraints: Dict
) -> Dict:
    """
    Decide Tech Radar ring placement using explicit heuristic rules.

    Decision is capped by risk and influenced by organizational constraints.

    Args:
        maturity_score: Normalized maturity score (0–1)
        trend: Output from tech_trend_tool
        risk: Output from risk_assessment_tool
        org_constraints: Output from org_context_tool

    Returns:
        Ring decision with confidence and justification
    """

    score = (
        maturity_score * 0.5
        + (0.3 if trend.get("momentum") == "increasing" else 0.1)
        - org_constraints.get("compliance_penalty", 0.0)
    )

    if score >= 0.75:
        proposed = "Adopt"
    elif score >= 0.5:
        proposed = "Trial"
    elif score >= 0.3:
        proposed = "Assess"
    else:
        proposed = "Hold"

    # ✅ SAFE DEFAULT
    ring_ceiling = risk.get("ring_ceiling", "Adopt")

    final_ring = min(
        proposed,
        ring_ceiling,
        key=lambda r: RING_ORDER.index(r)
    )

    return {
        "ring": final_ring,
        "confidence": round(min(1.0, score), 2),
        "justification": [
            f"Maturity score {maturity_score}",
            f"Momentum {trend.get('momentum')}",
            f"Risk level {risk.get('risk_level')}",
            f"Organization strictness {org_constraints.get('strictness')}",
        ],
    }

@tool(parse_docstring=True)
def generate_radar_tool(
    technologies: Dict[str, Dict],
    org_constraints: Dict
) -> Dict:
    """
    Generate final radar ring decisions using deterministic heuristics.

    This tool is called by the main agent after all technologies have been evaluated.

    Args:
        technologies: Mapping of technology name to evaluated data with maturity_score, trend, risk, and category
        org_constraints: Normalized organizational constraints from org_context_tool

    Returns:
        Final radar structure grouped by quadrant, mapping
        technology name to its assigned radar ring.
    """
    radar = {}

    for tech_name, data in technologies.items():
        decision = ring_decision_tool(
            maturity_score=data["maturity_score"],
            trend=data["trend"],
            risk=data["risk"],
            org_constraints=org_constraints,
        )

        quadrant = data["category"]
        radar.setdefault(quadrant, {})
        radar[quadrant][tech_name] = decision["ring"]

    return radar



@tool(parse_docstring=True)
def radar_consistency_tool(radar: Dict[str, str]) -> Dict:
    """
    Validate internal consistency of a generated Tech Radar.

    Flags structural or governance anomalies.

    Args:
        radar: Mapping of technology name to ring

    Returns:
        Consistency warnings, if any
    """
    warnings = []

    adopt_count = list(radar.values()).count("Adopt")
    if adopt_count > len(radar) * 0.4:
        warnings.append("Too many technologies in Adopt ring.")

    if "Hold" not in radar.values():
        warnings.append("No technologies marked as Hold.")

    return {
        "warnings": warnings,
        "is_consistent": len(warnings) == 0,
    }


@tool(parse_docstring=True)
def radar_export_tool(
    radar: Dict,
    format: Literal["markdown"] = "markdown"
) -> str:
    """
    Export a Tech Radar in a human-readable format.

    Currently supports Markdown export.

    Args:
        radar: Final radar structure
        format: Output format (default: markdown)

    Returns:
        Rendered Tech Radar
    """
    if format != "markdown":
        raise ValueError("Only markdown export is supported.")

    lines = ["# Technology Radar\n"]
    for quadrant, entries in radar.items():
        lines.append(f"## {quadrant}")
        for tech, ring in entries.items():
            lines.append(f"- **{tech}** → {ring}")
        lines.append("")

    return "\n".join(lines)

# ---------------------------------------------------------------------
# Data Fetchers
# ---------------------------------------------------------------------


GITHUB_API = "https://api.github.com"


def github_headers():
    """
    Headers for unauthenticated GitHub REST API usage.
    """
    return {
        "Accept": "application/vnd.github+json",
        "User-Agent": "tech-radar-agent"
    }

@tool(parse_docstring=True)
def github_repo_metrics_tool(
    owner: str,
    repo: str
) -> dict:
    """
    Fetch core GitHub repository metrics using the public REST API
    (no authentication).

    NOTE:
    - Subject to GitHub unauthenticated rate limits (60 req/hour).
    - Intended for low-frequency research use.

    Args:
        owner: GitHub organization or user name
        repo: Repository name

    Returns:
        TechnologyMetrics-compatible dictionary (partial fields populated)
    """
    with httpx.Client(headers=github_headers(), timeout=10.0) as client:
        # Repository metadata
        repo_resp = client.get(f"{GITHUB_API}/repos/{owner}/{repo}")
        repo_resp.raise_for_status()
        repo_data = repo_resp.json()

        # Contributors (first page only — acceptable heuristic)
        contributors_resp = client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/contributors",
            params={"per_page": 100}
        )
        contributors = len(contributors_resp.json())

        # Commits in last 30 days
        since = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
        commits_resp = client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/commits",
            params={"since": since, "per_page": 100}
        )
        monthly_commits = len(commits_resp.json())

        # Releases
        releases_resp = client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/releases",
            params={"per_page": 100}
        )
        releases = releases_resp.json()

        now = datetime.utcnow()
        monthly_releases = sum(
            1
            for r in releases
            if "published_at" in r
            and datetime.fromisoformat(
                r["published_at"].replace("Z", "")
            ) > now - timedelta(days=30)
        )

        # First release year
        if releases:
            first_release_year = datetime.fromisoformat(
                releases[-1]["published_at"].replace("Z", "")
            ).year
        else:
            first_release_year = datetime.fromisoformat(
                repo_data["created_at"].replace("Z", "")
            ).year

    return {
        "github_stars": repo_data["stargazers_count"],
        "monthly_commits": monthly_commits,
        "monthly_releases": monthly_releases,
        "breaking_changes": False,      # filled by release analysis tool
        "contributors": contributors,
        "enterprise_mentions": 0,       # filled by adoption tool
        "first_release_year": first_release_year,
    }

@tool(parse_docstring=True)
def github_release_analysis_tool(
    owner: str,
    repo: str
) -> dict:
    """
    Analyze GitHub releases for breaking-change signals using
    semantic versioning heuristics.

    Uses public GitHub REST API (no authentication).

    Args:
        owner: GitHub organization or user name
        repo: Repository name

    Returns:
        Dictionary containing breaking-change signal
    """
    with httpx.Client(headers=github_headers(), timeout=10.0) as client:
        resp = client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/releases",
            params={"per_page": 20}
        )
        resp.raise_for_status()
        releases = resp.json()

    major_versions = set()
    for r in releases:
        tag = r.get("tag_name", "")
        if tag.startswith("v"):
            tag = tag[1:]
        if "." in tag:
            major_versions.add(tag.split(".")[0])

    breaking_changes = len(major_versions) > 1

    return {
        "breaking_changes": breaking_changes
    }


@tool(parse_docstring=True)
def security_incidents_tool(
    owner: str,
    repo: str
) -> dict:
    """
    Fetch security-related signals for a repository using
    public GitHub endpoints.

    NOTE:
    - Unauthenticated access may not return private advisories.
    - Absence of data does NOT imply absence of risk.

    Args:
        owner: GitHub organization or user name
        repo: Repository name

    Returns:
        RiskMetrics-compatible dictionary (security-focused fields)
    """
    incidents = 0

    with httpx.Client(headers=github_headers(), timeout=10.0) as client:
        resp = client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/security-advisories"
        )
        if resp.status_code == 200:
            incidents = len(resp.json())

    return {
        "security_incidents": incidents,
        "api_instability": False,
        "vendor_lock_in": False,
        "cost_volatility": False,
        "safety_risk": incidents > 0,
    }

@tool(parse_docstring=True)
def enterprise_adoption_tool(
    technology: str
) -> int:
    """
    Estimate enterprise adoption via web signals.

    Uses Tavily search results as proxy signals.

    Args:
        technology: Name of the technology

    Returns:
        Count of enterprise adoption mentions
    """
    query = f"{technology} used by enterprise companies case study"
    results = tavily_client.search(query, max_results=5)

    return len(results.get("results", []))

@tool(parse_docstring=True)
def pricing_volatility_tool(
    pricing_page_url: str
) -> bool:
    """
    Detect pricing volatility from pricing page snapshots.

    NOTE: This is heuristic and should be backed by snapshot history.

    Args:
        pricing_page_url: URL of pricing page

    Returns:
        Boolean indicating pricing volatility
    """
    content = fetch_webpage_content(pricing_page_url)
    keywords = ["increase", "changed pricing", "deprecated", "sunset"]

    return any(k in content.lower() for k in keywords)
