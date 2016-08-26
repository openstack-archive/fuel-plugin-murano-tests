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


@test(groups=["plugin"])
class TestMuranoPostInstallation(api.MuranoPluginApi):
    """Class for testing that the Murano Detach plugin can be installed in an
    existing environment.
    """

    @test(depends_on_groups=["prepare_slaves_3"],
          groups=["deploy_environment_without_murano_plugin", "deploy",
                  "murano_plugin", "post_installation", 'murano'])
    @log_snapshot_after_test
    def deploy_environment_without_murano_plugin(self):
        """Deploy a cluster without the Murano Detach plugin.

        Scenario:
            1. Create the cluster
            2. Add 1 node with the controller role
            3. Add 1 node with the compute and cinder roles
            4. Upload the plugin to the master node
            5. Install the plugin
            6. Configure the plugin
            8. Deploy cluster
            8. Run OSTF

        Duration 60m
        Snapshot deploy_environment_without_murano_plugin
        """
        self.check_run("deploy_environment_without_murano_plugin")

        self.env.revert_snapshot("ready_with_3_slaves")

        self.prepare_plugin()

        self.helpers.create_cluster(name=self.__class__.__name__)

        self.activate_plugin()

        self.helpers.deploy_cluster({
            'slave-01': ['controller'],
            'slave-02': ['compute', 'cinder'],
        })

        self.run_ostf(['sanity', 'smoke', 'tests_platform'])

        self.env.make_snapshot("deploy_environment_without_murano_plugin",
                               is_make=True)

    @test(depends_on=[deploy_environment_without_murano_plugin],
          groups=["deploy_murano_plugin_in_existing_environment", "deploy",
                  "murano_plugin", "post_installation", 'murano'])
    @log_snapshot_after_test
    def deploy_murano_plugin_in_existing_environment(self):
        """Deploy the Murano Detach plugin in an existing environment.

        Scenario:
            1. Revert snapshot with deployed cluster
            2. Add 1 nodes with the plugin roles
            3. Deploy the cluster
            4. Check that Murano Detach plugin is running
            5. Run OSTF

        Duration 60m

        """
        self.check_run("deploy_murano_plugin_in_existing_environment")

        self.env.revert_snapshot("deploy_environment_without_murano_plugin")

        self.helpers.deploy_cluster({
            'slave-03': plugin_settings.role_name,
        })

        self.check_plugin_online()

        self.run_ostf(['sanity', 'smoke', 'tests_platform'])
