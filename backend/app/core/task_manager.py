from crewai import Crew, Process
from app.crew.job_market_analysis import JobMarketAnalysisCrew
from app.core.event_bus import event_bus

class TaskManager:
    def __init__(self, task_id: str, user_id: str, params: dict):
        self.task_id = task_id
        self.user_id = user_id
        self.params = params
    
    def emit_event(self, event_type: str, data: dict):
        try:
            event_bus.publish(self.task_id, {
                "type": event_type,
                "data": data
            })
        except Exception as e:
            print(f"Error emitting event: {e}")
    
    def run_crew(self):
        """Run the CrewAI analysis with event emission"""
        try:
            # Initialize crew with parameters
            crew = JobMarketAnalysisCrew(
                country=self.params['country'],
                city=self.params['city'],
                job_role=self.params['job_role'],
                include_skills=self.params['include_skills'],
                include_salaries=self.params['include_salaries'],
                include_companies=self.params['include_companies'],
                include_trends=self.params['include_trends'],
                event_callback=self.emit_event
            )
            
            # Run the crew
            self.emit_event("CREW_STARTED", {"message": "Analysis started"})
            result = crew.run()
            self.emit_event("CREW_COMPLETED", {"result": str(result)})
            return {"summary": "Crew run complete", "task": "success", "result": str(result)}
        except Exception as e:
            self.emit_event("CREW_ERROR", {"error": str(e)})
            raise