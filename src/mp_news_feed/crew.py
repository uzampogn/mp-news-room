"""
MpNewsFeed Crew - Analysis pipeline for pre-computed search results.

This crew handles Phase 2 of the pipeline:
1. content_filter - Filters and scores search results
2. context_researcher - Adds background context
3. summary_composer - Creates strategic report
4. email_distributor - Sends report via email

Note: Search is handled separately by SearchCrew via search_service.py
"""
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import List
from pydantic import BaseModel, Field
from crewai_tools import SerperDevTool
from mp_news_feed.tools.sendgrid_tool import SendGridEmailTool


class MpNewsResearch(BaseModel):
    """Detailed research on a MP activities"""
    mp_name: str = Field(description="MP name")
    article_title: str = Field(description="Article title")
    article_url: str = Field(description="Article URL")
    publication_date: str = Field(description="Publication date")
    source_name: str = Field(description="Source name")
    article_summary: str = Field(description="Short summary of the article")


class MpNewsResearchList(BaseModel):
    """A list of detailed research on all the MPs"""
    research_list: List[MpNewsResearch] = Field(description="Comprehensive research on all MPs")


class ContentFilteredItem(BaseModel):
    """A single filtered news item with score"""
    mp_name: str = Field(description="MP name")
    article_title: str = Field(description="Article title")
    article_url: str = Field(description="Article URL")
    publication_date: str = Field(description="Publication date")
    source_name: str = Field(description="Source name")
    article_summary: str = Field(description="Short summary of the article")
    relevance_score: int = Field(description="Relevance score 0-10")
    inclusion_reason: str = Field(description="Brief reason for inclusion")


class ContentFilteredList(BaseModel):
    """A list of relevant and filtered detailed research on all the MPs"""
    filtered_items: List[ContentFilteredItem] = Field(description="Filtered and scored news items")


class NewsContextItem(BaseModel):
    """A news item with added context"""
    mp_name: str = Field(description="MP name")
    article_title: str = Field(description="Article title")
    article_url: str = Field(description="Article URL")
    news_theme: str = Field(description="Theme of the news")
    background_context: str = Field(description="Background explanation")
    political_significance: str = Field(description="Why this matters politically")
    collaboration_angles: str = Field(description="Potential collaboration/advocacy angles")


class NewsContextList(BaseModel):
    """A list of contextualized news"""
    contextualized_items: List[NewsContextItem] = Field(description="News items with context")


@CrewBase
class MpNewsFeed():
    """MpNewsFeed crew - Analysis pipeline only (search handled by SearchCrew)"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def content_filter(self) -> Agent:
        return Agent(config=self.agents_config['content_filter'])

    @agent
    def context_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['context_researcher'],
            tools=[SerperDevTool()]
        )

    @agent
    def summary_composer(self) -> Agent:
        return Agent(config=self.agents_config['summary_composer'])

    @agent
    def email_distributor(self) -> Agent:
        return Agent(
            config=self.agents_config['email_distributor'],
            tools=[SendGridEmailTool()],
        )

    @task
    def filter_content_task(self) -> Task:
        return Task(
            config=self.tasks_config['filter_content_task'],
            output_pydantic=ContentFilteredList
        )

    @task
    def research_context_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_context_task'],
            output_pydantic=NewsContextList
        )

    @task
    def compose_summary_task(self) -> Task:
        return Task(config=self.tasks_config['compose_summary_task'])

    @task
    def distribute_report_task(self) -> Task:
        return Task(
            config=self.tasks_config['distribute_report_task'],
            max_retries=3,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the MpNewsFeed analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
