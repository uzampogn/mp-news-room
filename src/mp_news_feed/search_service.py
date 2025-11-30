"""
Search Service - Orchestrates parallel MP searches using SearchCrew.

This module provides the run_search() function that:
1. Takes a list of MPs
2. Runs SearchCrew.kickoff_for_each_async() to search each MP in parallel
3. Aggregates results into a single MpNewsResearchList format

This guarantees that every MP gets searched (Python controls iteration)
while preserving agent intelligence for query generation.
"""
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from mp_news_feed.search_crew import SearchCrew


async def run_search_async(
    mp_list: List[Dict[str, str]],
    timeframe: str = "8 months",
    today: str = None,
    max_concurrency: int = 10
) -> Dict[str, Any]:
    """
    Run parallel searches for all MPs using SearchCrew.

    Args:
        mp_list: List of dicts with 'name' and 'country' keys
        timeframe: How far back to search (e.g., "8 months")
        today: Today's date string (defaults to current date)
        max_concurrency: Max concurrent crew executions

    Returns:
        Dict with 'research_list' containing all search results
    """
    if today is None:
        today = datetime.now().strftime('%Y-%m-%d')

    # Build inputs for each MP
    inputs_list = [
        {
            "mp_name": mp["name"],
            "mp_country": mp["country"],
            "timeframe": timeframe,
            "today": today,
        }
        for mp in mp_list
    ]

    print(f"Starting parallel search for {len(inputs_list)} MPs...")
    print(f"Max concurrency: {max_concurrency}")

    # Run SearchCrew for each MP in parallel with concurrency control
    search_crew = SearchCrew()
    crew = search_crew.crew()
    # Set max_rpm to limit API rate (helps avoid rate limits)
    crew.max_rpm = max_concurrency * 20  # Approximate requests per minute
    results = await crew.kickoff_for_each_async(inputs=inputs_list)

    print(f"Search complete. Processing {len(results)} results...")

    # Aggregate results into MpNewsResearchList format
    research_list = []
    for result in results:
        if result and hasattr(result, 'pydantic'):
            mp_result = result.pydantic
            # Convert each article to MpNewsResearch format
            for article in mp_result.articles:
                research_list.append({
                    "mp_name": mp_result.mp_name,
                    "article_title": article.title,
                    "article_url": article.url,
                    "publication_date": article.publication_date,
                    "source_name": article.source,
                    "article_summary": article.summary,
                })
        elif result and hasattr(result, 'raw'):
            # Fallback if pydantic parsing failed - try to extract from raw
            print(f"Warning: Result returned raw output instead of pydantic: {result.raw[:200]}...")

    print(f"Aggregated {len(research_list)} total articles from {len(results)} MPs")

    return {
        "research_list": research_list,
        "mp_count": len(mp_list),
        "search_date": today,
        "timeframe": timeframe,
    }


def run_search(
    mp_list: List[Dict[str, str]],
    timeframe: str = "8 months",
    today: str = None,
    max_concurrency: int = 10
) -> Dict[str, Any]:
    """
    Synchronous wrapper for run_search_async().

    Args:
        mp_list: List of dicts with 'name' and 'country' keys
        timeframe: How far back to search (e.g., "8 months")
        today: Today's date string (defaults to current date)
        max_concurrency: Max concurrent crew executions

    Returns:
        Dict with 'research_list' containing all search results
    """
    return asyncio.run(
        run_search_async(mp_list, timeframe, today, max_concurrency)
    )
