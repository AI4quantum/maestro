#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

"""
    Simple test code to inspect the agent module
    For debug only
    """ 

import sys
sys.path.append("agents/crewai/activity-planner")

from activity_planner import ActivityPlannerCrew
import inspect

print(inspect.getmembers(ActivityPlannerCrew()))


