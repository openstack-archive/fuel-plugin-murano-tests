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
class TestMuranoPluginBvt(api.MuranoPluginApi):
    """Class for bvt testing the Murano plugin."""

    @test(depends_on_groups=['prepare_slaves_3'],
          groups=["deploy_murano_plugin", "deploy",
                  "murano", "bvt"])
    @log_snapshot_after_test
    def deploy_murano_plugin(self):
        """Deploy a cluster with the Murano plugin

        Scenario:
            1. Upload the Murano plugin to the master node
            2. Install the plugin
            3. Create the cluster
            4. Add 1 node with controller role
            5. Add 1 node with compute and cinder roles
            6. Add 1 node with murano-node roles
            7. Deploy the cluster
            8. Run OSTF

        Duration 90m
        Snapshot deploy_murano_plugin
        """
        self.check_run("deploy_murano_plugin")

        self.env.revert_snapshot("ready_with_3_slaves")

        self.prepare_plugin()

        self.helpers.create_cluster(name=self.__class__.__name__)

        self.activate_plugin()

        self.helpers.deploy_cluster(self.base_nodes)

        self.run_ostf()

        self.env.make_snapshot("deploy_murano_plugin", is_make=True)

    @test(depends_on_groups=['prepare_slaves_5'],
          groups=["deploy_murano_plugin_ha", "deploy",
                  "murano", "bvt"])
    @log_snapshot_after_test
    def deploy_murano_plugin_ha(self):
        """Deploy a cluster with the Murano plugin

        Scenario:
            1. Upload the Murano plugin to the master node
            2. Install the plugin
            3. Create the cluster
            4. Add 3 node with controller role
            5. Add 1 node with compute and cinder roles
            6. Add 1 node with compute and murano-node roles
            7. Deploy the cluster
            8. Run OSTF

        Duration 120m
        Snapshot deploy_murano_plugin_ha
        """
        self.check_run("deploy_murano_plugin_ha")

        self.env.revert_snapshot("ready_with_5_slaves")

        self.prepare_plugin()

        self.helpers.create_cluster(name=self.__class__.__name__)

        self.activate_plugin()

        self.helpers.deploy_cluster(self.ha_nodes)

        self.run_ostf()

        self.env.make_snapshot("deploy_murano_plugin_ha", is_make=True)

    @test(depends_on=[deploy_murano_plugin],
          groups=["uninstall_deployed_murano_plugin", "uninstall",
                  "murano_plugin", "smoke"])
    @log_snapshot_after_test
    def uninstall_deployed_murano_plugin(self):
        """Uninstall the Murano plugin with a deployed environment

        Scenario:
            1.  Try to remove the plugins using the Fuel CLI
            2.  Check plugins can't be uninstalled on deployed cluster.
            3.  Remove the environment.
            4.  Remove the plugins.

        Duration 20m
        """
        self.env.revert_snapshot("deploy_murano_plugin")

        self.check_uninstall_failure()

        self.fuel_web.delete_env_wait(self.helpers.cluster_id)

        self.uninstall_plugin()

    @test(depends_on_groups=["prepare_slaves_3"],
          groups=["uninstall_murano_plugin", "uninstall", "murano_plugin",
                  "smoke"])
    @log_snapshot_after_test
    def uninstall_murano_plugin(self):
        """Uninstall the Murano plugin

        Scenario:
            1.  Install the plugins.
            2.  Remove the plugins.

        Duration 5m
        """
        self.env.revert_snapshot("ready_with_3_slaves")

        self.prepare_plugin()

        self.uninstall_plugin()
