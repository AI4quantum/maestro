#!/usr/bin/env python
"""
This script uses the crew.ai framework to find activities suitable for cold or wet weather. 

Dependencies:
- crewai
- langchain_community

Usage:
- Ensure ollama is available on localhost:11434 and the llama3.1 model is available.
- Run the script to get a list of 5 activities to do in cole weather in San Francisco.
"""

from crewai import Agent, Crew, Task, Process, LLM
from crewai.project import CrewBase, agent, task, crew
from crewai.tools import tool

# Many ways of using tools - using custom tool from langchain
from langchain_community.tools import DuckDuckGoSearchRun

@CrewBase
class ColdWeatherCrew:
    """
    Defines a class to manage a crew that finds activities to do in cold or wet weather.
    """

    # setup LLM
    llm = LLM(model="ollama/llama3.1", base_url="http://localhost:11434")

    @tool("DuckDuckGo")
    def ddg_search(question: str) -> str:
        """
        Defines a crew.ai tool which performs a web search using the 
        DuckDuckGo search engine.

        Args:
            question (str): The search query to be sent to DuckDuckGo.

        Returns:
            str: The search results returned by DuckDuckGo.
        """
        search_tool = DuckDuckGoSearchRun()
        return search_tool.run(question)

    @agent
    def activity_planner_agent(self) -> Agent:
        """
        Defines a crew.ai agent that plans activities using the specified 
        agent configuration and tools.

        Returns:
            Agent: An instance of the Agent class configured with the activity planner settings,
                   including the DuckDuckGo search tool and a locally running LLM (Ollama 3.1).
        """
        return Agent(
            config=self.agents_config["activity_planner_agent"],
            tools=[self.ddg_search],  # Include the DuckDuckGo search tool
            # Hardcode to ollama 3.1 running locally
            llm=self.llm,
            verbose=True,
        )

    @task
    def activity_finder_task(self) -> Task:
        """
        Defines a task to find activities suitable for cold weather.
    
        Returns:
            Task: A Task object configured with the activity finder task settings.
        """
        return Task(config=self.tasks_config["activity_finder_task"], verbose=True)

    @crew
    def activity_crew(self) -> Crew:
        """
        Creates and returns a Crew object configured with the current agents, tasks, 
        and a sequential process.

        Returns:
            Crew: A Crew object with the specified agents, tasks, and process.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

# Main for testing
if __name__ == "__main__":
    print("Running crew...")
    inputs = {"location": "San Francisco"}
    ColdWeatherCrew().activity_crew().kickoff(inputs=inputs)
