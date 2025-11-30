"""
Search Crew - Handles searching for a SINGLE MP.

This crew is designed to be run via kickoff_for_each_async() to guarantee
that every MP gets searched. Each execution handles exactly one MP,
preserving the agent's intelligence for query generation while ensuring
deterministic iteration via Python control.
"""
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field
from typing import List

from mp_news_feed.tools.date_filtered_serper import DateFilteredSerperTool

# Explicit LLM to avoid defaulting to Anthropic
SEARCH_LLM = LLM(model="gpt-4o-mini", temperature=0.3)


class ArticleResult(BaseModel):
    """A single search result article"""
    title: str = Field(description="Article title")
    url: str = Field(description="Article URL")
    publication_date: str = Field(description="Publication date")
    source: str = Field(description="Source name")
    summary: str = Field(description="Brief summary of the article")


class MPSearchResult(BaseModel):
    """Search results for a single MP"""
    mp_name: str = Field(description="MP name")
    country: str = Field(description="MP country")
    articles: List[ArticleResult] = Field(description="List of articles found")


@CrewBase
class SearchCrew():
    """
    Crew for searching a SINGLE MP.

    Designed to be run via kickoff_for_each_async() with inputs like:
    [{"mp_name": "John Doe", "mp_country": "Germany", "timeframe": "8 months"}, ...]

    This preserves agent intelligence for query generation while guaranteeing
    that Python controls iteration over all MPs.
    """

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/search_tasks.yaml'

    @agent
    def search_orchestrator(self) -> Agent:
        return Agent(
            config=self.agents_config['search_orchestrator'],
            tools=[DateFilteredSerperTool(months_back=8)],
            llm=SEARCH_LLM,  # Explicit LLM to avoid Anthropic default
        )

    @task
    def search_single_mp_task(self) -> Task:
        return Task(
            config=self.tasks_config['search_single_mp_task'],
            output_pydantic=MPSearchResult
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
