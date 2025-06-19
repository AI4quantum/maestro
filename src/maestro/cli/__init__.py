# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

"""CLI module initialization and path configuration."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../cli")
