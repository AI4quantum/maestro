#!/usr/bin/env python

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

"""
This script uses the crew.ai framework to find activities suitable for cold or wet weather. 

Dependencies:
- crewai

Usage:
- Ensure ollama is available on localhost:11434 and the llama3.1 model is available.
"""

import os
from crewai import Agent, Crew, Task, Process, LLM
from crewai.project import CrewBase, agent, task, crew
from crewai.tools import tool

@CrewBase
class Generic_Crew:
    """
    Defines a class to manage a crew that finds activities to do in cold or wet weather.
    """

    # TODO Set model/URL from configuration
    llm = LLM(
        model=os.getenv("MAESTRO_DEMO_OLLAMA_MODEL", "ollama/llama3.1"),
        base_url=os.getenv("MAESTRO_DEMO_OLLAMA_URL", "http://localhost:11434")
    )

    @agent
    def generic_crew_agent(self) -> Agent:
        """
        Defines a crew.ai agent that plans activities using the specified
        agent configuration and tools.

        Returns:
            Agent: An instance of the Agent class configured with the activity planner settings,
                   including the DuckDuckGo search tool and a locally running LLM (Ollama 3.1).
        """
        return Agent(
            config=self.agents_config["generic_crew_agent"],
            llm=self.llm,  # Use the locally running LLM (Ollama 3.1)
            verbose=False,
        )

    @task
    def generic_crew_task(self) -> Task:
        """
        Defines a task to find activities suitable for cold weather.

        Returns:
            Task: A Task object configured with the activity finder task settings.
        """
        return Task(config=self.tasks_config["generic_task"], verbose=False)

    @crew
    def generic_crew(self) -> Crew:
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

    
