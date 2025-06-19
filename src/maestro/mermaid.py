#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

class Mermaid:
    # kind: sequenceDiagram or flowchart
    # orientation: TD (top down), RL (right left)
    def __init__(self, workflow, kind="sequenceDiagram", orientation="TD"):
        self.workflow = workflow
        self.kind = kind
        self.orientation = orientation

    def to_markdown(self) -> str:
        if self.kind == "sequenceDiagram":
            return self.__to_sequenceDiagram()
        elif self.kind == "flowchart":
            return self.__to_flowchart()
        else:
            raise RuntimeError(f"Invalid Mermaid kind: {self.kind}")

    def __fix_agent_name(self, name):
        return name.replace("-", "_")

    def __agent_for_step(self, step_name):
        for step in self.workflow['spec']['template']['steps']:
            if step['name'] == step_name:
                return step.get('agent')
        return None

    # returns a markdown of the workflow as a mermaid sequence diagram
    # 
    # sequenceDiagram
    # participant agent1
    # participant agent2
    #
    # agent1->>agent2: step1
    # agent2->>agent3: step2
    # agent2-->>agent1: step3
    # agent1->>agent3: step4
    #
    # See mermaid sequence diagram documentation: 
    # https://mermaid.js.org/syntax/sequenceDiagram.html

    def __sequence_participants(self):
        tpl = self.workflow['spec']['template']
        agents = tpl.get('agents')
        if agents:
            return agents
        seen = []
        for step in tpl.get('steps', []):
            a = step.get('agent')
            if not a:
                continue
            if any(k in step for k in ("inputs", "context", "outputs")):
                continue
            if a not in seen:
                seen.append(a)
        return seen

    def __to_sequenceDiagram(self) -> str:
        sb = "sequenceDiagram\n"
        # participants
        for agent in self.__sequence_participants():
            sb += f"participant {self.__fix_agent_name(agent)}\n"

        steps = self.workflow['spec']['template'].get('steps', [])
        agentL = None
        for i, step in enumerate(steps):
            # skip scoring/context-only steps
            if any(k in step for k in ("inputs", "context", "outputs")):
                continue
            # update agentL only when this step names a real agent
            if step.get('agent'):
                agentL = self.__fix_agent_name(step['agent'])

            # find next real agent for the arrow
            agentR = None
            for nxt in steps[i+1:]:
                if any(k in nxt for k in ("inputs", "context", "outputs")):
                    continue
                if nxt.get('agent'):
                    agentR = self.__fix_agent_name(nxt['agent'])
                break

            if agentR:
                sb += f"{agentL}->>{agentR}: {step['name']}\n"
            else:
                sb += f"{agentL}->>{agentL}: {step['name']}\n"

            # condition / parallel / loop
            if step.get('condition'):
                for cond in step['condition']:
                    sb += self.__to_sequenceDiagram_condition(agentL, agentR, cond)
            if step.get('parallel'):
                sb += self.__to_sequenceDiagram_parallel(agentL, step)
            if step.get('loop'):
                sb += self.__to_sequenceDiagram_loop(agentL, step['loop'])

        # global cron-event block
        event = self.workflow['spec']['template'].get('event')
        if event and 'cron' in event:
            sb += self.__to_sequenceDiagram_event(event)

        # global exception block
        exc = self.workflow['spec']['template'].get('exception')
        if exc:
            sb += self.__to_sequenceDiagram_exception(
                self.workflow['spec']['template'].get('steps', []), exc
            )

        return sb

    def __to_sequenceDiagram_event(self, event):
        name  = event.get('name')
        cron  = event.get('cron')
        exit  = event.get('exit')
        sb    = f"alt cron \"{cron}\"\n"
        if event.get('steps'):
            for step_name in event['steps']:
                sb += f"  cron->>{self.__agent_for_step(step_name)}: {step_name}\n"
        else:
            agent = event.get('agent')
            sb += f"  cron->>{agent}: {name}\n"
        sb += "else\n"
        sb += f"  cron->>exit: {exit}\n"
        sb += "end\n"
        return sb

    def __to_sequenceDiagram_parallel(self, agentL, parallelStep):
        sb = "par\n"
        for i, agent in enumerate(parallelStep['parallel']):
            agentR = self.__fix_agent_name(agent)
            sb += f"  {agentL}->>{agentR}: {parallelStep['name']}\n"
            if i < len(parallelStep['parallel']) - 1:
                sb += "and\n"
        sb += "end\n"
        return sb

    def __to_sequenceDiagram_loop(self, agentL, loopDef):
        expr = loopDef.get('until', 'True')
        sb   = f"loop {expr}\n"
        sb  += f"  {agentL}-->{self.__fix_agent_name(loopDef['agent'])}: {('until' if 'until' in loopDef else 'loop')}\n"
        sb  += "end\n"
        return sb

    def __to_sequenceDiagram_condition(self, agentL, agentR, condition):
        sb = ""
        if condition.get('case'):
            cond = condition['case']
            do   = condition.get('do', '')
            if condition.get('default'):
                cond = 'default'
                do   = condition['default']
            sb += f"{agentL}->>{agentR}: {do} {cond}\n"
        elif condition.get('if'):
            if_expr   = condition['if']
            then_expr = condition.get('then', '')
            else_expr = condition.get('else')
            sb       += f"{agentL}->>{agentR}: {if_expr}\n"
            sb       += "alt if True\n"
            sb       += f"  {agentL}->>{agentR}: {then_expr}\n"
            if else_expr:
                sb   += "else is False\n"
                sb   += f"  {agentR}->>{agentL}: {else_expr}\n"
            sb       += "end\n"
        return sb

    def __to_sequenceDiagram_exception(self, steps, exception):
        sb = "alt exception\n"
        for step in steps:
            if step.get('agent'):
                agentL = self.__fix_agent_name(step['agent'])
                sb    += f"  {agentL}->>{exception['agent']}: {exception['name']}\n"
        sb += "end"
        return sb

    def __to_flowchart(self) -> str:
        sb    = f"flowchart {self.orientation}\n"
        steps = self.workflow['spec']['template'].get('steps', [])
        i     = 0
        while i < len(steps):
            step = steps[i]
            # skip scoring/context-only steps
            if any(k in step for k in ("inputs", "context", "outputs")):
                i += 1
                continue

            aL = step.get('agent')
            # find next real step
            aR = None
            for nxt in steps[i+1:]:
                if any(k in nxt for k in ("inputs", "context", "outputs")):
                    continue
                aR = nxt.get('agent')
                break

            if aR:
                sb += f"{aL}-- {step['name']} -->{aR}\n"
            else:
                sb += f"{aL}-- {step['name']} -->{aL}\n"

            if step.get('condition'):
                for cond in step['condition']:
                    sb += self.__to_flowchart_condition(aL, aR, step, cond)
            i += 1

        exc = self.workflow['spec']['template'].get('exception')
        if exc:
            sb += self.__to_flowchart_exception(steps, exc)
        return sb

    def __to_flowchart_condition(self, agentL, agentR, step, condition):
        sb = ""
        if condition.get('case'):
            cond = condition['case']
            do   = condition.get('do', '')
            if condition.get('default'):
                cond = 'default'
                do   = condition['default']
            sb += f"{agentL}-- {do} {cond} -->{agentR}\n"
        if condition.get('if'):
            expr = condition['if']
            then = condition.get('then', '')
            els  = condition.get('else', '')
            sb  += f"{step['name']} --> Condition{{\"{expr}\"}}\n"
            sb  += f"  Condition -- Yes --> {then}\n"
            sb  += f"  Condition -- No --> {els}\n"
        return sb

    def __to_flowchart_event(self, event):
        return ""

    def __to_flowchart_exception(self, steps, exception):
        sb = ""
        for step in steps:
            if step.get('agent'):
                agentL = self.__fix_agent_name(step['agent'])
                sb    += f"{agentL} -->|exception| {exception['name']}{{{exception['agent']}}}\n"
        return sb
