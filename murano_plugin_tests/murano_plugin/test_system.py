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


@test(groups=["plugins"])
class TestSystemMuranoPlugin(api.MuranoPluginApi):
    """Class for system tests for Murano Detach plugin."""

    @test(depends_on_groups=["deploy_murano_plugin_full_ha"],
          groups=["check_scaling_murano", "scaling",
                  "murano", "system",
                  "add_remove_controller_compute_murano"])
    @log_snapshot_after_test
    def add_remove_controller_compute_murano(self):
        """Verify that the number of controllers and
        computes can scale up and down.

        Scenario:
            1. Revert snapshot with 9 deployed nodes in HA configuration
            2. Remove one controller node and update the cluster
            3. Check that plugin is working
            4. Run OSTF
            5. Add one controller node (return previous state) and
               update the cluster
            6. Check that plugin is working
            7. Run OSTF
            8. Remove one compute node and update the cluster
            9. Check that plugin is working
            10. Run OSTF
            11. Add one compute node (return previous state) and
                update the cluster
            12. Check that plugin is working
            13. Run OSTF

        Duration 240m
        Snapshot add_remove_controller_compute_murano
        """
        self.env.revert_snapshot("deploy_murano_plugin_full_ha")

        controller_manipulated_node = {'slave-03': ['controller']}

        # Remove controller
        self.helpers.remove_nodes_from_cluster(controller_manipulated_node)

        self.check_plugin_online()

        self.run_ostf(['sanity', 'smoke', 'ha'])

        compute_manipulated_node = {'slave-04': ['compute', 'ceph-osd']}

        # Remove compute
        self.helpers.remove_nodes_from_cluster(compute_manipulated_node,
                                               redeploy=False)
        self.set_replication_factor(replicas="2")
        self.helpers.apply_changes()

        self.check_plugin_online()

        self.run_ostf(['sanity', 'smoke', 'ha'])

        # Add controller
        # NOTE(rpromyshlennikov): test can fail here before
        # bug https://bugs.launchpad.net/fuel/+bug/1603480 isn't fixed
        # and not merged in devops, here and elsewhere on node adding.
        self.helpers.add_nodes_to_cluster(controller_manipulated_node)

        self.check_plugin_online()

        self.run_ostf(['sanity', 'smoke', 'ha'])

        # Add compute
        self.helpers.add_nodes_to_cluster(compute_manipulated_node,
                                          redeploy=False)
        self.set_replication_factor(replicas="3")
        self.helpers.apply_changes()

        self.check_plugin_online()

        self.run_ostf(['sanity', 'smoke', 'ha'])

        self.env.make_snapshot("add_remove_controller_compute_murano",
                               is_make=False)

    @test(depends_on_groups=["deploy_murano_plugin_full_ha"],
          groups=["check_scaling_murano", "scaling",
                  "murano", "system",
                  "add_remove_murano_node"])
    @log_snapshot_after_test
    def add_remove_murano_node(self):
        """Verify that the number of Murano Detach nodes
        can scale up and down.

        Scenario:
            1. Revert snapshot with 9 deployed nodes in HA configuration
            2. Remove one Murano Detach node and update the cluster
            3. Check that plugin is working
            4. Run OSTF
            5. Add one Murano Detach node (return previous state) and
               update the cluster
            6. Check that plugin is working
            7. Run OSTF

        Duration 120m
        Snapshot add_remove_murano_node
        """
        self.env.revert_snapshot("deploy_murano_plugin_full_ha")

        manipulated_node = {'slave-07': self.settings.role_name}

        # Remove Murano Detach node
        self.helpers.remove_nodes_from_cluster(manipulated_node)

        self.check_plugin_online()

        self.run_ostf(['sanity', 'smoke', 'ha'])

        # Add Murano Detach node
        self.helpers.add_nodes_to_cluster(manipulated_node)

        self.check_plugin_online()

        self.run_ostf(['sanity', 'smoke', 'ha'])

        self.env.make_snapshot("add_remove_murano_node", is_make=False)
