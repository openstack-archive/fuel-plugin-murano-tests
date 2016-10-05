#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from fuelweb_test.helpers.decorators import log_snapshot_after_test
from proboscis import test

from murano_plugin_tests.murano_plugin import api


@test(groups=["plugin"])
class TestMuranoFailover(api.MuranoPluginApi):
    """Class for testing that the Murano Detach plugin works properly
    on controller or detached node fail.
    """

    def _test_failover(self, operation, role_name, snapshot_name):
        self.env.revert_snapshot(snapshot_name)

        self.check_plugin_failover(operation, role_name)

        self.run_ostf(['sanity', 'smoke', 'check_plugin_online'])

    @test(depends_on_groups=["deploy_murano_plugin"],
          groups=["failover", "murano", "system", "destructive",
                  "soft_reboot_murano_node"])
    @log_snapshot_after_test
    def soft_reboot_murano_node(self):
        """Verify that failover for Murano plugin works
        on Murano detached node soft_reboot.

        Scenario:
            1. Soft reboot murano node.
            2. Check that plugin is working.
            3. Run OSTF.

        Duration 30m
        Snapshot soft_reboot_murano_node
        """
        self._test_failover("soft_reboot", self.settings.role_name,
                            "deploy_murano_plugin")

    @test(depends_on_groups=["deploy_murano_plugin"],
          groups=["failover", "murano", "system", "destructive",
                  "hard_reboot_murano_node"])
    @log_snapshot_after_test
    def hard_reboot_murano_node(self):
        """Verify that failover for Murano plugin works
        on Murano detached node power off.

        Scenario:
            1. Hard reboot murano node.
            2. Check that plugin is working.
            3. Run OSTF.

        Duration 30m
        Snapshot hard_reboot_murano_node
        """
        self._test_failover("hard_reboot", self.settings.role_name,
                            "deploy_murano_plugin")

    @test(depends_on_groups=["deploy_murano_plugin_on_controller"],
          groups=["failover", "murano", "system", "destructive",
                  "soft_reboot_controller_node_murano_plugin"])
    @log_snapshot_after_test
    def soft_reboot_controller_node_murano_plugin(self):
        """Verify that failover for Murano plugin works
        on controller node soft_reboot.

        Scenario:
            1. Soft reboot controller node.
            2. Check that plugin is working.
            3. Run OSTF.

        Duration 30m
        Snapshot soft_reboot_controller_node_murano_plugin
        """
        self._test_failover("soft_reboot", ["controller"],
                            "deploy_murano_plugin_on_controller")

    @test(depends_on_groups=["deploy_murano_plugin_on_controller"],
          groups=["failover", "murano", "system", "destructive",
                  "hard_reboot_controller_node_murano_plugin"])
    @log_snapshot_after_test
    def hard_reboot_controller_node_murano_plugin(self):
        """Verify that failover for Murano plugin works
        on controller node power off.

        Scenario:
            1. Hard reboot controller node.
            2. Check that plugin is working.
            3. Run OSTF.

        Duration 30m
        Snapshot hard_reboot_controller_node_murano_plugin
        """
        self._test_failover("hard_reboot", ["controller"],
                            "deploy_murano_plugin_on_controller")
