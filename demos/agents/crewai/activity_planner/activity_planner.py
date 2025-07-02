#!/usr/bin/env python

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

"""
This script uses the crew.ai framework to find activities suitable for cold or wet weather.

Dependencies:
- crewai
- langchain_community

Usage:
- Ensure ollama is available on localhost:11434 and the llama3.1 model is available.
- Run the script to get a list of 5 activities to do in cole weather in San Francisco.
"""

# TODO Make a more representative crew agent. This is simple
# TODO decorators use config/agents.yaml & config/tasks.yaml. Former clashes in name which causes yaml validation error
# TODO decorators cause PyLance errors

import os
from crewai import Agent, Crew, Task, Process, LLM
from crewai.project import CrewBase, agent, task, crew
from crewai.tools import tool

# Many ways of using tools - using custom tool from langchain
from langchain_community.tools import DuckDuckGoSearchRun


@CrewBase
class ActivityPlannerCrew:
    """
    Defines a class to manage a crew that finds activities to do in cold or wet weather.
    """

    # TODO Set model/URL from configuration
    llm = LLM(
        model=os.getenv("MAESTRO_DEMO_OLLAMA_MODEL", "ollama/llama3.1"),
        base_url=os.getenv("MAESTRO_DEMO_OLLAMA_URL", "http://localhost:11434"),
    )

    @tool("DuckDuckGo")
    # TODO PyLance issue - missing self() but fails with crewai decorators if added
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
            # tools=[self.ddg_search],  # Include the DuckDuckGo search tool
            llm=self.llm,  # Use the locally running LLM (Ollama 3.1)
            verbose=False,
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
            # TODO: disable verbose when working well
            verbose=False,
        )


# Main for testing
if __name__ == "__main__":
    print("Running crew...")
    inputs = {"prompt": "Show me some places to visit in cold weather in San Francisco"}
    crew_output = ActivityPlannerCrew().activity_crew().kickoff(inputs=inputs)
    print("\n====\n\nFinal raw output returned by agent:\n====\n\n")
    print(crew_output.raw)
