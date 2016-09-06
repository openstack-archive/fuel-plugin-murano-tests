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
from murano_plugin_tests.murano_plugin import plugin_settings


@test(groups=["plugins"])
class TestMuranoPluginUpdate(api.MuranoPluginApi):
    """Class for testing upgrades for Murano plugin."""

    @test(depends_on_groups=["prepare_slaves_3"],
          groups=["deploy_murano_out_of_the_box", "murano"])
    @log_snapshot_after_test
    def deploy_murano_out_of_the_box(self):
        """Deploy Murano out of the box and run OSTF tests

        Scenario:
            1. Deploy Fuel Cluster with one controller and Murano
            2. Run OSTF
            3. Make snapshot

        Duration 90m
        Snapshot deploy_murano_out_of_the_box
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        self.helpers.create_cluster(name=self.__class__.__name__,
                                    settings={'murano': True})

        self.helpers.deploy_cluster(self.only_controllers)

        self.helpers.run_ostf(['sanity', 'smoke', 'tests_platform'])

        self.env.make_snapshot("deploy_murano_out_of_the_box", is_make=True)

    @test(depends_on=[deploy_murano_out_of_the_box],
          groups=["deploy_murano_and_plugin", "murano_plugin_upgrade",
                  "murano",
                  "deploy_murano_plugin_in_environment_with_murano"])
    @log_snapshot_after_test
    def deploy_murano_plugin_in_environment_with_murano(self):
        """Upgrade Murano via plugin and run OSTF tests.

        Scenario:
            1. Revert shapshot with box murano installation
            2. Upload plugin to master node
            3. Install plugin
            4. Activate plugin
            5. Update cluster (Deploy changes)
            6. Run OSTF

        Duration 60m
        Snapshot deploy_murano_plugin_in_environment_with_murano
        """
        self.env.revert_snapshot("deploy_murano_out_of_the_box")

        self.prepare_plugin()

        self.activate_plugin()

        self.helpers.apply_changes()

        self.helpers.run_ostf(['sanity', 'smoke', 'tests_platform'])

        self.env.make_snapshot(
            "deploy_murano_plugin_in_environment_with_murano",
            is_make=False)

    @test(depends_on=[deploy_murano_out_of_the_box],
          groups=["deploy_murano_and_plugin_add_role", "deploy",
                  "murano", "murano_plugin_upgrade",
                  "deploy_murano_plugin_in_environment_with_murano"])
    @log_snapshot_after_test
    def deploy_murano_node_in_environment_with_murano(self):
        """Upgrade Murano via plugin (adding murano-node) and run OSTF tests.

        Scenario:
            1. Revert shapshot with box murano installation
            2. Upload plugin to master node
            3. Install plugin
            4. Activate plugin and add new node
               with murano-node role to the cluster
            5. Update cluster (Deploy changes)
            6. Run OSTF

        Duration 75m
        Snapshot deploy_murano_node_in_environment_with_murano
        """

        self.env.revert_snapshot("deploy_murano_out_of_the_box")

        self.prepare_plugin()

        self.activate_plugin()

        self.helpers.add_nodes_to_cluster({
            'slave-03': plugin_settings.role_name,
        })

        self.helpers.run_ostf(['sanity', 'smoke', 'tests_platform'])

        self.env.make_snapshot("deploy_murano_node_in_environment_with_murano",
                               is_make=False)
