#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os, yaml, unittest

from unittest import TestCase

from maestro.mermaid import Mermaid
from maestro.workflow import Workflow

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
            '  cron->>exit: ( "test" in input  )',
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
                #TODO complete
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
            'participant test5',
            'participant test2',
            'participant test3',
            'test2->>test5: step2',
            'test5->>test3: step1',
            'test3->>test3: step3',
            'alt cron "* * * * *"',
            '  cron->>test2: step2',
            '  cron->>test5: step1',
            'else',
            '  cron->>exit: (input.get("final_prompt").find("This is a test input") != -1)',
            'end',
            'alt exception',
            '  test2->>test2: step2',
            '  test5->>test2: step2',
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
                #TODO: complete
                ]
            for m in expected_markdown:
                self.assertTrue(m in markdown)

class TestMermaid_parallel(TestCase):
    def setUp(self):        
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/parallel_workflow.yaml"))[0]

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
            'participant test5',
            'test1->>test1: list',
            'test1->>test5: parallel',
            'test5->>test5: result',
            'par',
            '  test1->>test2: parallel',
            'and',
            '  test1->>test3: parallel',
            'and',
            '  test1->>test4: parallel',
            'end',
            'alt exception',
            '  test1->>test4: step4',
            '  test5->>test4: step4',
            'end']
        for m in expected_markdown:
            self.assertTrue(m in markdown)

    def test_markdown_flowchart(self):
        for orientation in ["TD", "LR"]:
            mermaid = Mermaid(self.workflow_yaml, "flowchart", f"{orientation}")
            self.assertTrue(mermaid.to_markdown().startswith(f"flowchart {orientation}"))
            markdown = mermaid.to_markdown()
            expected_markdown = [
                f"flowchart {orientation}",
                #TODO: complete
                ]
            for m in expected_markdown:
                self.assertTrue(m in markdown)

class TestMermaid_loop(TestCase):
    def setUp(self):        
        self.workflow_yaml = parse_yaml(os.path.join(os.path.dirname(__file__),"../yamls/workflows/loop_workflow.yaml"))[0]

    def tearDown(self):
        self.workflow_yaml = None

    def test_markdown_sequenceDiagram(self):
        mermaid = Mermaid(self.workflow_yaml, "sequenceDiagram")
        markdown = mermaid.to_markdown()
        expected_markdown = [
            'sequenceDiagram',
            'participant generate1_10',
            'participant countdown',
            'generate1_10->>generate1_10: step1',
            'generate1_10->>generate1_10: step2',
            'loop (input.find("happy") != -1)',
            '  generate1_10-->countdown: until',
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
                #TODO: complete
                ]
            for m in expected_markdown:
                self.assertTrue(m in markdown)

if __name__ == '__main__':
    unittest.main()
