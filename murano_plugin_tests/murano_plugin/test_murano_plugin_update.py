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
          groups=["deploy_murano_and_plugin", "upgrade",
                  "murano"])
    @log_snapshot_after_test
    def deploy_murano_plugin_in_environment_with_murano(self):
        """Upgrade Murano via plugin and run OSTF tests.

        Scenario:
            1. Deploy Fuel Cluster with one controller and Murano
            2. Run OSTF
            3. Upload plugin to master node
            4. Install plugin
            5. Activate plugin
            6. Update cluster (Deploy changes)
            7. Run OSTF

        Duration 90m
        Snapshot deploy_environment_with_murano_plugin
        """

        self.check_run("deploy_environment_with_murano_plugin")

        self.env.revert_snapshot("ready_with_3_slaves")

        self.helpers.create_cluster(name=self.__class__.__name__,
                                    settings={'murano': True})

        self.helpers.deploy_cluster({
            'slave-01': ['controller'],
            'slave-02': ['compute'],
        })

        self.helpers.run_ostf(['sanity', 'smoke', 'tests_platform'])

        self.prepare_plugin()

        self.activate_plugin()

        self.helpers.deploy_cluster({
            'slave-01': ['controller'],
            'slave-02': ['compute'],
        })

        self.check_plugin_online()

        self.helpers.run_ostf(['sanity', 'smoke', 'tests_platform'])

        self.env.make_snapshot("deploy_environment_with_murano_plugin",
                               is_make=True)

    @test(depends_on_groups=["prepare_slaves_3"],
          groups=["deploy_murano_and_plugin_add_role", "deploy",
                  "murano"])
    @log_snapshot_after_test
    def deploy_murano_node_in_environment_with_murano(self):
        """Upgrade Murano via plugin (adding murano-node) and run OSTF tests.

        Scenario:
            1. Deploy Fuel Cluster with one controller and Murano
            2. Run OSTF
            3. Upload plugin to master node
            4. Install plugin
            5. Activate plugin and add new node
               with murano-node role to the cluster
            6. Update cluster (Deploy changes)
            7. Run OSTF

        Duration 120m
        Snapshot deploy_murano_node_in_environment_with_murano
        """
        self.check_run("deploy_murano_node_in_environment_with_murano")

        self.env.revert_snapshot("ready_with_3_slaves")

        self.helpers.create_cluster(name=self.__class__.__name__,
                                    settings={'murano': True})

        self.helpers.deploy_cluster({
            'slave-01': ['controller'],
            'slave-02': ['compute'],
        })

        self.helpers.run_ostf(['sanity', 'smoke', 'tests_platform'])

        self.prepare_plugin()

        self.activate_plugin(['sanity', 'smoke', 'tests_platform'])

        self.helpers.deploy_cluster({
            'slave-03': plugin_settings.role_name,
        })

        self.check_plugin_online()

        self.helpers.run_ostf()

        self.env.make_snapshot("deploy_murano_node_in_environment_with_murano",
                               is_make=True)
