"""
Custom Serper Tool with Date Filtering.

This tool extends the standard Serper API to include time-based filtering
using the `tbs` parameter to restrict results to a specific time period.
"""
import os
import requests
from typing import Optional
from crewai.tools import BaseTool
from pydantic import Field


class DateFilteredSerperTool(BaseTool):
    """
    A custom Serper search tool that filters results by date.

    Uses the `tbs` parameter to restrict Google search results
    to a specific time period (e.g., past 8 months).
    """

    name: str = "Search the internet with date filter"
    description: str = (
        "Search the internet for recent news articles within a specific time period. "
        "Use this tool to find news about MPs and their activities. "
        "Results are filtered to show only recent articles."
    )

    api_key: Optional[str] = Field(default=None, description="Serper API key")
    months_back: int = Field(default=8, description="Number of months to search back")
    n_results: int = Field(default=10, description="Number of results to return")

    def __init__(self, months_back: int = 8, n_results: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.api_key = os.getenv("SERPER_API_KEY")
        self.months_back = months_back
        self.n_results = n_results

    def _run(self, search_query: str) -> str:
        """
        Execute the search with date filtering.

        Args:
            search_query: The search query string

        Returns:
            Search results as formatted string
        """
        if not self.api_key:
            return "Error: SERPER_API_KEY environment variable not set"

        url = "https://google.serper.dev/search"

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        # Use tbs parameter for time-based filtering
        # qdr:m8 = past 8 months, qdr:m6 = past 6 months, etc.
        payload = {
            "q": search_query,
            "num": self.n_results,
            "tbs": f"qdr:m{self.months_back}"  # Filter to past N months
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Format results for the agent
            results = []

            if "organic" in data:
                for item in data["organic"]:
                    result = {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "date": item.get("date", "Unknown"),
                        "position": item.get("position", 0)
                    }
                    results.append(result)

            if not results:
                return f"No results found for: {search_query}"

            return str({"searchParameters": payload, "organic": results})

        except requests.exceptions.RequestException as e:
            return f"Search error: {str(e)}"
