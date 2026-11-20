from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools.tools.file_read_tool.file_read_tool import FileReadTool
from crewai_tools.tools.scrape_website_tool.scrape_website_tool import (
    ScrapeWebsiteTool,
)

RESUME_PATH = str(Path(__file__).resolve().parent / "resume.md")


@CrewBase
class JobApplicationAgents():
    """JobApplicationAgents crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    def __init__(self, resume_path: str = RESUME_PATH, output_dir: str = "") -> None:
        # resume_path: the resume the strategist may read (the tool is locked to this file).
        # output_dir: relative folder for the .md outputs; "" keeps them in the project root.
        self.resume_path = resume_path
        self.output_dir = output_dir

    def _out(self, name: str) -> str:
        return f"{self.output_dir}/{name}" if self.output_dir else name

    @agent
    def job_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['job_analyst'], # type: ignore[index]
            tools=[ScrapeWebsiteTool()], #reads the job posting from its URL
            verbose=True
        )

    @agent
    def resume_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['resume_strategist'], # type: ignore[index]
            tools=[FileReadTool(file_path=self.resume_path)],
            verbose=True
        )

    @agent
    def cover_letter_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['cover_letter_writer'], # type: ignore[index]
            verbose=True
        )

    @agent
    def interview_coach(self) -> Agent:
        return Agent(
            config=self.agents_config['interview_coach'], # type: ignore[index]
            verbose=True
        )

    @agent
    def application_critics(self) -> Agent:
        return Agent(
            config=self.agents_config['application_critics'], # type: ignore[index]
            verbose=True
        )

    @task
    def analyze_job_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_job_task'], # type: ignore[index]
        )

    @task
    def tailor_resume_task(self) -> Task:
        return Task(
            config=self.tasks_config['tailor_resume_task'], # type: ignore[index]
            output_file=self._out('tailored_report.md')
        )

    @task
    def cover_letter_task(self) -> Task:
        return Task(
            config=self.tasks_config['cover_letter_task'], # type: ignore[index]
            output_file=self._out('cover_letter.md')
        )

    @task
    def interview_prep_task(self) -> Task:
        return Task(
            config=self.tasks_config['interview_prep_task'], # type: ignore[index]
            output_file=self._out('interview_prep.md')
        )

    @task
    def match_report_task(self) -> Task:
        return Task(
            config=self.tasks_config['match_report_task'], # type: ignore[index]
            output_file=self._out('match_report.md')
        )

    @crew
    def crew(self) -> Crew:
        """Creates the JobApplicationAgents crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
