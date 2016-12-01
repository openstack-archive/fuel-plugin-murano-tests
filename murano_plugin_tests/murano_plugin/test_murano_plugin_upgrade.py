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
class TestMuranoPluginUpgrade(api.MuranoPluginApi):
    """Class for upgrade testing the Murano plugin."""

    @test(depends_on_groups=["prepare_slaves_3"],
          groups=["upgrade_murano_plugin_on_controller",
                  "deploy", "murano_plugin", "upgrade", 'murano'])
    @log_snapshot_after_test
    def upgrade_murano_plugin_on_controller(self):
        """Upgrade old Murano Plugin via the new one on controller.

        Scenario:
            1. Upload the Murano plugin(version 1.1.0) to the master node
            2. Install the plugin
            3. Create the cluster
            4. Add 1 node with controller role
            5. Add 1 node with compute and cinder roles
            6. Deploy the cluster
            7. Run OSTF
            8. Upload new version of the Murano plugin to the master node
            9. Install new plugin
            10. Upgrade old version of the plugin on the controller
            11. Update cluster
            12. Run OSTF

        Duration 120m
        Snapshot upgrade_murano_plugin_on_controller
        """

        self.env.revert_snapshot("ready_with_3_slaves")

        self.helpers.add_and_enable_yum_repo_with_detach_plugin()

        self.helpers.install_detach_murano_plugin_from_repository(
            'detach-murano-1.1.noarch')

        self.helpers.create_cluster(name=self.__class__.__name__)

        self.activate_plugin('detach-murano', '1.1.0')

        self.helpers.deploy_cluster(self.only_controllers)

        self.run_ostf(['sanity', 'smoke'])
        self.check_plugin_online()

        self.prepare_plugin()

        self.activate_plugin()

        self.helpers.apply_changes()

        self.run_ostf(['sanity', 'smoke'])
        self.check_plugin_online()

    @test(depends_on_groups=["prepare_slaves_3"],
          groups=["upgrade_murano_plugin_on_murano_node",
                  "deploy", "murano_plugin", "upgrade", 'murano'])
    @log_snapshot_after_test
    def upgrade_murano_plugin_on_murano_node(self):
        """Upgrade old Murano Plugin via the new one with adding murano-node.

        Scenario:
            1. Upload the Murano plugin(version 1.1.0) to the master node
            2. Install the plugin
            3. Create the cluster
            4. Add 1 node with controller role
            5. Add 1 node with compute and cinder roles
            6. Deploy the cluster
            7. Run OSTF
            8. Upload new version of the Murano plugin to the master node
            9. Install new plugin
            10. Add 1 node with compute and murano-node roles
            11. Upgrade old version of the plugin
            12. Update cluster
            13. Run OSTF

        Duration 120m
        Snapshot upgrade_murano_plugin_on_murano_node
        """

        self.env.revert_snapshot("ready_with_3_slaves")

        self.helpers.add_and_enable_yum_repo_with_detach_plugin()

        self.helpers.install_detach_murano_plugin_from_repository(
            'detach-murano-1.1.noarch')

        self.helpers.create_cluster(name=self.__class__.__name__)

        self.activate_plugin('detach-murano', '1.1.0')

        self.helpers.deploy_cluster(self.only_controllers)

        self.run_ostf(['sanity', 'smoke'])
        self.check_plugin_online()

        self.prepare_plugin()

        self.activate_plugin()

        self.helpers.deploy_cluster({
            'slave-03': plugin_settings.role_name,
        })

        self.run_ostf(['sanity', 'smoke'])
        self.check_plugin_online()
