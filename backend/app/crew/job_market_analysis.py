from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from langchain_openai import ChatOpenAI
from typing import List, Callable, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import re
import json
import requests
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()


@tool
def tavily_search(query: str) -> str:
    """Search for job market data using Tavily API"""
    from langchain_tavily import TavilySearch
    tavily = TavilySearch(api_key=os.getenv("TAVILY_API_KEY"))
    end_date = str(datetime.now().strftime("%Y-%m-%d"))
    start_date = str((datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"))
    return tavily.run({
        "query": query,
        "search_depth": "advanced",
        "include_domains": ["linkedin.com", "indeed.com", "glassdoor.com", "naukri.com"],
        "max_results": 15,
        "include_answer": True,
        "start_date":start_date,
        "end_date":end_date
    })

@CrewBase
class JobMarketAnalysisCrew:
    """Crew for analyzing job markets in specific locations"""

    agents: List[Agent]
    tasks: List[Task]
    
    llm = ChatOpenAI(
        model="ollama/mistral-nemo:12b",
        base_url="http://localhost:11434"
    )

    def __init__(
        self,
        country: str = "India",
        city: str = "Bangalore",
        job_role: str = "Software Engineer",
        include_skills: bool = True,
        include_salaries: bool = True,
        include_companies: bool = True,
        include_trends: bool = True,
        event_callback: Optional[Callable] = None
    ):
        self.country = country
        self.city = city
        self.job_role = job_role
        self.include_skills = include_skills
        self.include_salaries = include_salaries
        self.include_companies = include_companies
        self.include_trends = include_trends
        self.event_callback = event_callback
        
        print(f"\nStarting analysis for {self.job_role} jobs in {self.city}, {self.country}")
        
        # Calculate date range for comparisons
        self.end_date = datetime.now().strftime("%Y-%m-%d")
        self.start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        
        # Initialize tools
        self.search_tools = [tavily_search]

    ## TOOLS ##

    

    ## EVENT HANDLING ##
    
    def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event if callback is provided"""
        if self.event_callback:
            self.event_callback(event_type, data)
    
    def agent_callback(self, step_output: str, agent_name: str, task_description: str ):
        """Callback function for agent actions"""
        print(step_output,agent_name,task_description)
        self.emit_event("AGENT_ACTION", {
            "agent": agent_name,
            "task": task_description,
            "step": str(step_output)
        })
    
    def task_callback(self, task_name: str, status: str):
        """Callback function for task status"""
        print(task_name,status)
        self.emit_event("TASK_STATUS", {
            "task": task_name,
            "status": status
        })

    ## AGENTS ##
    
    @agent
    def job_market_researcher(self) -> Agent:
        return Agent(
            role="Job Market Researcher",
            goal=f"Gather current and historical job market data for {self.job_role} in {self.city}, {self.country}",
            backstory=(
                "Expert in labor market analysis with 10+ years experience tracking employment trends. "
                "Specializes in extracting and validating job market statistics from diverse sources."
            ),
            verbose=True,
            tools=self.search_tools,
            llm=self.llm,
            max_iter=3,
            max_execution_time=600,
            allow_delegation=False,
            step_callback=lambda step: self.agent_callback(
                step, 
                "Job Market Researcher", 
                "Gathering job market data"
            )
        )
    
    @agent
    def data_analyst(self) -> Agent:
        return Agent(
            role="Data Analyst",
            goal="Analyze job market trends and compare locations",
            backstory=(
                "Statistical analyst with expertise in employment data. "
                "Skilled at identifying patterns and making data-driven comparisons."
            ),
            verbose=True,
            llm=self.llm,
            max_iter=3,
            max_execution_time=300,
            allow_delegation=False,
            step_callback=lambda step: self.agent_callback(
                step, 
                "Data Analyst", 
                "Analyzing market trends"
            )
        )
    
    @agent
    def city_comparison_specialist(self) -> Agent:
        return Agent(
            role="City Comparison Specialist",
            goal=f"Compare job markets for {self.job_role} across cities in {self.country}",
            backstory=(
                "Economic geographer specializing in regional employment disparities. "
                "Uses multi-city data to identify optimal locations for specific roles."
            ),
            verbose=True,
            llm=self.llm,
            max_iter=3,
            max_execution_time=600,
            allow_delegation=False,
            step_callback=lambda step: self.agent_callback(
                step, 
                "City Comparison Specialist", 
                "Comparing cities"
            )
        )
        
    @agent
    def job_market_reporter(self) -> Agent:
        return Agent(
            role="Job Market Reporter",
            goal="Compile comprehensive job market reports",
            backstory=(
                "Professional business reporter with focus on employment trends. "
                "Translates complex data into actionable insights for job seekers."
            ),
            verbose=True,
            llm=self.llm,
            max_iter=3,
            max_execution_time=600,
            allow_delegation=False,
            step_callback=lambda step: self.agent_callback(
                step, 
                "Job Market Reporter", 
                "Compiling report"
            )
        )
    
    @agent
    def quality_assurance_editor(self) -> Agent:
        return Agent(
            role="Quality Assurance Editor",
            goal="Ensure report accuracy and clarity",
            backstory=(
                "Detail-oriented editor with background in labor economics. "
                "Verifies data sources and improves presentation of complex information."
            ),
            verbose=True,
            llm=self.llm,
            max_iter=3,
            max_execution_time=600,
            allow_delegation=False,
            step_callback=lambda step: self.agent_callback(
                step, 
                "Quality Assurance Editor", 
                "Reviewing report"
            )
        )

    ## TASKS ##

    @task
    def research_current_market(self) -> Task:
        description = f"""
        Research the CURRENT job market for {self.job_role} in {self.city}, {self.country}:
        - Number of active job openings
        - Distribution of experience levels (entry, mid, senior)
        - Employment types (full-time, contract, etc.)
        - Primary industries hiring for this role
        
        Use ONLY reliable sources:
        - Official employment portals
        - Major job boards (LinkedIn, Indeed, Glassdoor)
        - Government labor statistics
        - Industry reports
        
        Timeframe: Last 365 days
        """
        
        expected_output = f"""
        Structured JSON with:
        - current_openings: int
        - experience_distribution: dict (entry/mid/senior)
        - employment_types: dict
        - top_industries: list
        - source_urls: list
        """
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=self.job_market_researcher(),
            tools=self.search_tools,
            # output_json=True,
            callback=lambda _: self.task_callback("Research Current Market", "started")
        )

    @task
    def research_historical_trends(self) -> Task:
        description = f"""
        Research HISTORICAL trends for {self.job_role} in {self.city}, {self.country}:
        - Number of openings 6 months ago
        - Number of openings 1 year ago
        - Percentage change over time
        - Key events that impacted the job market (layoffs, expansions, etc.)
        
        Timeframe: {self.start_date} to {self.end_date}
        """
        
        expected_output = f"""
        Structured JSON with:
        - openings_6mo: int
        - openings_1yr: int
        - pct_change_6mo: float
        - pct_change_1yr: float
        - significant_events: list
        - source_urls: list
        """
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=self.job_market_researcher(),
            context=[self.research_current_market()],
            # output_json=True,
            callback=lambda _: self.task_callback("Research Historical Trends", "started")
        )
    
    @task
    def analyze_market_dynamics(self) -> Task:
        description = f"""
        Analyze the job market dynamics for {self.job_role} in {self.city}:
        - Calculate growth/decline rates
        - Identify seasonal patterns
        - Determine market competitiveness
        - Assess hiring velocity (time-to-fill positions)
        
        Use data from current and historical research.
        """
        
        expected_output = f"""
        JSON with analysis:
        - growth_rate: float
        - seasonal_patterns: str
        - competitiveness_index: float (1-10)
        - avg_time_to_fill: int (days)
        - market_outlook: str (positive/neutral/negative)
        """
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=self.data_analyst(),
            context=[self.research_historical_trends()],
            # output_json=True,
            callback=lambda _: self.task_callback("Analyze Market Dynamics", "started")
        )
    
    @task
    def compare_cities(self) -> Task:
        description = f"""
        Compare the job market for {self.job_role} in {self.city} with 3 other major cities in {self.country}:
        - Identify cities with better opportunities
        - Compare number of openings
        - Compare salary ranges
        - Compare growth rates
        - Highlight key advantages of each location
        
        Include at least:
        - 1 city with stronger market
        - 1 city with comparable market
        - 1 city with weaker market
        """
        
        expected_output = f"""
        JSON with comparison data:
        - comparison_cities: list of 3 cities
        - openings_comparison: dict (city: openings)
        - salary_comparison: dict (city: salary_range)
        - growth_comparison: dict (city: growth_rate)
        - top_city_recommendation: str
        - source_urls: list
        """
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=self.city_comparison_specialist(),
            context=[self.analyze_market_dynamics()],
            # output_json=True,
            callback=lambda _: self.task_callback("Compare Cities", "started")
        )
    
    @task
    def compile_report(self) -> Task:
        description = f"""
        Compile a comprehensive report on the job market for {self.job_role} in {self.city}, {self.country}:
        - Current market status
        - Historical trends and changes
        - City comparison analysis
        - Future outlook
        
        Additional information to include based on user selection:
        {self.get_additional_info_section()}
        
        Structure:
        1. Executive Summary
        2. Current Market Snapshot
        3. Historical Trends
        4. City Comparison
        5. Future Outlook
        6. Actionable Recommendations
        
        Format: Markdown with clear section headings and data tables
        """
        
        expected_output = """
        Well-structured markdown report with:
        - Key statistics in tables
        - Visual trend representations (using text-based charts)
        - Clear section headings
        - Data sources and references
        """
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=self.job_market_reporter(),
            context=[
                self.research_current_market(),
                self.research_historical_trends(),
                self.analyze_market_dynamics(),
                self.compare_cities()
            ],
            callback=lambda _: self.task_callback("Compile Report", "started")
        )
    
    @task
    def review_report(self) -> Task:
        description = f"""
        Perform final review of the job market report:
        - Verify all statistics and sources
        - Ensure clear explanations of trends
        - Check city comparison fairness
        - Validate actionable recommendations
        - Improve readability for non-technical audience
        """
        
        expected_output = "Polished final report ready for delivery"
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=self.quality_assurance_editor(),
            context=[self.compile_report()],
            callback=lambda _: self.task_callback("Review Report", "started")
        )
    
    def get_additional_info_section(self) -> str:
        """Generate description of additional info based on user selection"""
        sections = []
        if self.include_skills:
            sections.append("- In-demand skills and qualifications")
        if self.include_salaries:
            sections.append("- Detailed salary ranges by experience level")
        if self.include_companies:
            sections.append("- Top companies hiring for this role")
        if self.include_trends:
            sections.append("- Emerging trends and future predictions")
        
        return "\n".join(sections) if sections else "None"

    ## CREW ##

    @crew
    def crew(self) -> Crew:
        """Creates the Job Market Analysis crew"""
        # Emit crew started event
        self.emit_event("CREW_STARTED", {
            "country": self.country,
            "city": self.city,
            "job_role": self.job_role,
            "start_date": self.start_date,
            "end_date": self.end_date
        })
        
        return Crew(
            agents=[
                self.job_market_researcher(),
                self.data_analyst(),
                self.city_comparison_specialist(),
                self.job_market_reporter(),
                self.quality_assurance_editor()
            ],
            tasks=[
                self.research_current_market(),
                self.research_historical_trends(),
                self.analyze_market_dynamics(),
                self.compare_cities(),
                self.compile_report(),
                self.review_report()
            ],
            process=Process.sequential,
            verbose=True,
            memory=False,
            full_output=True
        )
    
    def run(self) -> str:
        try:
            crew_instance = self.crew()
            result = crew_instance.kickoff()

            # Emit final event
            self.emit_event("CREW_COMPLETED", {
                "status": "success",
                "result": str(result)
            })

            return str(result)
        except Exception as e:
            self.emit_event("CREW_ERROR", {"error": str(e)})
            raise
