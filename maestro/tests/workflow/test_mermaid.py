#!/usr/bin/env python3

# Copyright © 2025 IBM
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, yaml, unittest

from unittest import TestCase

from src.mermaid import Mermaid
from src.workflow import Workflow

def parse_yaml(file_path):
    with open(file_path, "r") as file:
        yaml_data = list(yaml.safe_load_all(file))
    return yaml_data

# Workflow::to_mermaid
class TestWorkflow_to_mermaid(TestCase):
    def setUp(self):        
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/simple_workflow.yaml"))[0]
        self.workflow = Workflow({}, self.workflow_yaml)
        
    def tearDown(self):
        self.workflow_yaml = None
        self.workflow = None

    def test_markdown_sequenceDiagram(self):
        markdown = self.workflow.to_mermaid("sequenceDiagram")
        expected_markdown = [
                "sequenceDiagram",
                "participant test1",
                "participant test2",
                "participant test3",
                "test1->>test2: step1",
                "test2->>test3: step2",
                "test3->>test3: step3"
            ]
        for m in expected_markdown:
            self.assertTrue(m in markdown)

    def test_markdown_flowchart(self):
        for orientation in ["TD", "LR"]:
            markdown = self.workflow.to_mermaid("flowchart", f"{orientation}")
            expected_markdown = [
                    f"flowchart {orientation}",
                    "test1-- step1 -->test2",
                    "test2-- step2 -->test3",
                    "test3-- step3 -->test3"
                ]
            for m in expected_markdown:
                self.assertTrue(m in markdown)

# Mermaid
class TestMermaid(TestCase):
    def setUp(self):        
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/simple_workflow.yaml"))[0]
        
    def tearDown(self):
        self.workflow_yaml = None

    def test_markdown_sequenceDiagram(self):
        mermaid = Mermaid(self.workflow_yaml, "sequenceDiagram")
        markdown = mermaid.to_markdown()
        expected_markdown = [
                "sequenceDiagram",
                "participant test1",
                "participant test2",
                "participant test3",
                "test1->>test2: step1",
                "test2->>test3: step2",
                "test3->>test3: step3"
            ]
        for m in expected_markdown:
            self.assertTrue(m in markdown)

    def test_markdown_flowchart(self):
        for orientation in ["TD", "LR"]:        
            mermaid = Mermaid(self.workflow_yaml, "flowchart", f"{orientation}")
            markdown = mermaid.to_markdown()
            expected_markdown = [
                    f"flowchart {orientation}",
                    "test1-- step1 -->test2",
                    "test2-- step2 -->test3",
                    "test3-- step3 -->test3"
                ]
            for m in expected_markdown:
                self.assertTrue(m in markdown)

class TestMermaidCondition_case(TestCase):
    def setUp(self):        
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/conditional_case_workflow.yaml"))[0]
        
    def tearDown(self):
        self.workflow_yaml = None

    #
    # # expected mermaid code
    # sequenceDiagram
    # sequenceDiagram
    # participant agent1
    # participant agent2
    # participant agent3
    # agent1->>agent2: step1
    # agent2->>agent3: step2
    # agent3->>agent3: step3
    # agent3->>None: step2 (input.some_condition == True)
    # agent3->>None: step3 (input.some_condition == False)
    # agent3->>None: step3 default
    # 
    def test_markdown_sequenceDiagram(self):
        mermaid = Mermaid(self.workflow_yaml, "sequenceDiagram")
        markdown = mermaid.to_markdown()
        expected_markdown = [
            "sequenceDiagram",
                "participant agent1",
                "participant agent2",
                "participant agent3",
                "agent1->>agent2: step1",
                "agent2->>agent3: step2",
                "agent3->>agent3: step3",
                "agent3->>None: step2 (input.some_condition == True)",
                "agent3->>None: step3 (input.some_condition == False)"
            ]
        for m in expected_markdown:
            self.assertTrue(m in markdown)

    #
    # # expected mermaid code
    # flowchart LR #or TD
    # agent1-- step1 -->agent2
    # agent2-- step2 -->agent3
    # agent3-- step2 (input.some_condition == True) -->agent2
    # agent3-- step3 (input.some_condition == False) -->agent3
    #
    # TODO: complete
    def _test_markdown_flowchart(self):
        for orientation in ["TD", "LR"]:
            mermaid = Mermaid(self.workflow_yaml, "flowchart", f"{orientation}")
            self.assertTrue(mermaid.to_markdown().startswith(f"flowchart {orientation}"))

            self.assertTrue(f"agent1-- step1 -->agent2" in mermaid.to_markdown())
            self.assertTrue(f"agent3-- step2 (input.some_condition == True) -->agent2" in mermaid.to_markdown())
            self.assertTrue(f"agent3-- step3 (input.some_condition == False) -->agent3" in mermaid.to_markdown())

class TestMermaidCondition_if(TestCase):
    def setUp(self):        
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/conditional_if_workflow.yaml"))[0]
        
    def tearDown(self):
        self.workflow_yaml = None
    
    def test_markdown_sequenceDiagram(self):
        mermaid = Mermaid(self.workflow_yaml, "sequenceDiagram")
        markdown = mermaid.to_markdown()
        expected_markdown = [
            "sequenceDiagram",
            "participant agent1",
            "participant agent2",
            "participant agent3",
            "agent1->>agent2: step1",
            "agent1->>agent2: (input.some_condition == True)",
            "alt if True",
                "agent1->>agent2: step2",
            "else is False",
                "agent2->>agent1: step3",
            "end",
            "agent2->>agent3: step2",
            "agent3->>agent3: step3",
        ]
        for m in expected_markdown:
            self.assertTrue(m in markdown)
    
    def test_markdown_flowchart(self):
        for orientation in ["TD", "LR"]:
            mermaid = Mermaid(self.workflow_yaml, "flowchart", f"{orientation}")
            self.assertTrue(mermaid.to_markdown().startswith(f"flowchart {orientation}"))
            markdown = mermaid.to_markdown()
            expected_markdown = [
                f"flowchart {orientation}",
                    "agent1-- step1 -->agent2",
                    "step1 --> Condition{\"(input.some_condition == True)\"}",
                        "Condition -- Yes --> step2",
                        "Condition -- No --> step3",
                    "agent2-- step2 -->agent3",
                    "agent3-- step3 -->agent3",
                ]
            for m in expected_markdown:
                self.assertTrue(m in markdown)

class TestMermaid_exception(TestCase):
    def setUp(self):        
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/simple_workflow.yaml"))[0]

    def tearDown(self):
        self.workflow_yaml = None

    def test_markdown_sequenceDiagram(self):
        mermaid = Mermaid(self.workflow_yaml, "sequenceDiagram")
        markdown = mermaid.to_markdown()
        expected_markdown = [
            'sequenceDiagram',
            'participant test1',
            'participant test2',
            'participant test3',
            'participant test4',
            'test1->>test2: step1',
            'test2->>test3: step2',
            'test3->>test3: step3',
            'alt exception',
            '  test1->>test4: step4',
            '  test2->>test4: step4',
            '  test3->>test4: step4',
            'end'
        ]
        for m in expected_markdown:
            self.assertTrue(m in markdown)

    def test_markdown_flowchart(self):
        for orientation in ["TD", "LR"]:
            mermaid = Mermaid(self.workflow_yaml, "flowchart", f"{orientation}")
            self.assertTrue(mermaid.to_markdown().startswith(f"flowchart {orientation}"))
            markdown = mermaid.to_markdown()
            expected_markdown = [
                f"flowchart {orientation}",
                    "test1-- step1 -->test2",
                    "test2-- step2 -->test3",
                    "test3-- step3 -->test3",
                    "test1 -->|exception| step4{test4}",
                    "test2 -->|exception| step4{test4}",
                    "test3 -->|exception| step4{test4}"
                ]
            for m in expected_markdown:
                self.assertTrue(m in markdown)

class TestMermaid_event_cron(TestCase):
    def setUp(self):        
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/simple_cron_workflow.yaml"))[0]

    def tearDown(self):
        self.workflow_yaml = None

    def test_markdown_sequenceDiagram(self):
        mermaid = Mermaid(self.workflow_yaml, "sequenceDiagram")
        markdown = mermaid.to_markdown()
        expected_markdown = [
            'sequenceDiagram',
            'participant test1',
            'participant test2',
            'participant test3',
            'participant test4',
            'test2->>test2: step1',
            'test2->>test3: step2',
            'test3->>test1: step3',
            'test1->>test1: step4',
            'alt cron "10 14 * * 1"',
            '  cron->>test4: cron event',
            'else',
            '  cron->>exit: ( input.count >= 3 )',
            'end',
            'alt exception',
            '  test2->>test2: step2',
            '  test2->>test2: step2',
            '  test3->>test2: step2',
            '  test1->>test2: step2',
            'end'
        ]
        for m in expected_markdown:
            self.assertTrue(m in markdown)

    def test_markdown_flowchart(self):
        for orientation in ["TD", "LR"]:
            mermaid = Mermaid(self.workflow_yaml, "flowchart", f"{orientation}")
            self.assertTrue(mermaid.to_markdown().startswith(f"flowchart {orientation}"))
            markdown = mermaid.to_markdown()
            expected_markdown = [
                f"flowchart {orientation}",
                ]
            for m in expected_markdown:
                self.assertTrue(m in markdown)

class TestMermaid_event_cron_many_steps(TestCase):
    def setUp(self):
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/simple_cron_many_steps_workflow.yaml"))[0]

    def tearDown(self):
        self.workflow_yaml = None

    def test_markdown_sequenceDiagram(self):
        mermaid = Mermaid(self.workflow_yaml, "sequenceDiagram")
        markdown = mermaid.to_markdown()
        expected_markdown = [
            'sequenceDiagram',
            'participant test1',
            'participant test2',
            'participant test3',
            'test2->>test2: step1',
            'test2->>test3: step2',
            'test3->>test3: step3',
            'alt cron "10 14 * * 1"',
            '  cron->>test2: step2',
            '  cron->>test3: step3',
            'else',
            '  cron->>exit: ( input.exit == True )',
            'end',
            'alt exception',
            '  test2->>test2: step2',
            '  test2->>test2: step2',
            '  test3->>test2: step2',
            'end'
        ]
        for m in expected_markdown:
            self.assertTrue(m in markdown)

    def test_markdown_flowchart(self):
        for orientation in ["TD", "LR"]:
            mermaid = Mermaid(self.workflow_yaml, "flowchart", f"{orientation}")
            self.assertTrue(mermaid.to_markdown().startswith(f"flowchart {orientation}"))
            markdown = mermaid.to_markdown()
            expected_markdown = [
                f"flowchart {orientation}",
                ]
            for m in expected_markdown:
                self.assertTrue(m in markdown)

if __name__ == '__main__':
    unittest.main()
