# /usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

import os
import requests

import pytest
import unittest
from unittest import TestCase
from maestro.deploy import Deploy


# `deploy` tests
class TestDeploy(TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.deploy = Deploy(
            "tests/examples/condition_agents.yaml",
            "tests/examples/condition_workflow.yaml",
            "BEE_API_KEY=sk-proj-testkey BEE_API=http://192.168.86.45:4000 DRY_RUN=1",
        )

    def tearDown(self):
        self.deploy = None

    @pytest.mark.skipif(
        os.getenv("DEPLOY_KUBERNETES_TEST") != "1", reason="Kubernetes deploy skipped"
    )
    def test_deploy_to_kubernetes(self):
        self.deploy.deploy_to_kubernetes()
        if os.getenv("IN_GITHUB_ACTION") != "1":
            response = requests.get("http://127.0.0.1:30051/").text
            self.assertTrue(response.find("Running expert...") != -1)
            self.assertTrue(response.find("Running colleague...") != -1)

    @pytest.mark.skipif(
        os.getenv("DEPLOY_DOCKER_TEST") != "1", reason="Docker deploy skipped"
    )
    def test_deploy_to_docker(self):
        self.deploy.deploy_to_docker()
        if os.getenv("IN_GITHUB_ACTION") != "1":
            response = requests.get("http://127.0.0.1:5000/").text
            self.assertTrue(response.find("Running expert...") != -1)
            self.assertTrue(response.find("Running colleague...") != -1)


if __name__ == "__main__":
    unittest.main()
