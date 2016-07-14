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
from murano_plugin_tests.murano_plugin import api
from plugin_settings import base_nodes
from proboscis import test



@test(groups=["plugins"])
class TestMuranoPluginBvt(api.MuranoPluginApi):
    """Class for bvt testing the Murano plugin."""

    @test(depends_on_groups=['prepare_slaves_5'],
          groups=["deploy_murano_bvt", "deploy",
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
        Snapshot deploy_murano_bvt
        """
        self.check_run("deploy_ceilometer_redis")
        self.env.revert_snapshot("ready_with_5_slaves")

        self.prepare_plugin()

        self.helpers.create_cluster(name=self.__class__.__name__)

        self.activate_plugin()

        self.helpers.deploy_cluster(base_nodes)

        self.run_ostf()

        self.env.make_snapshot("deploy_murano_bvt", is_make=True)
