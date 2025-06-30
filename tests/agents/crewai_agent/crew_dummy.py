# Dummy class for testing crewai loader
# SPDX-License-Identifier: Apache-2.0


class CrewOutput:
    raw: str


class Crew:
    # TODO: kickoff actually takes & returns a dict[str,str]
    # def kickoff(inputs: dict[str, str]) -> str:
    def kickoff(self, inputs: dict[str, str]) -> CrewOutput:
        print("Running kickoff method")
        print(inputs)
        crewout = CrewOutput()
        crewout.raw = "OK"
        return crewout


class DummyCrew:
    def dummy_crew(self) -> Crew:
        print("Getting a Crew to return")
        return Crew()
