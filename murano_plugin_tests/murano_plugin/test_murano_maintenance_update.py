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
class TestMuranoPluginMU(api.MuranoPluginApi):
    """Class for Maintenance Update testing the Murano plugin."""

    @test(depends_on_groups=["deploy_murano_plugin"],
          groups=["test_MU_upgrade", "murano"])
    @log_snapshot_after_test
    def test_mu_upgrade_murano_node(self):
        """ Apply MU over cluster with plugin and Murano node

        Scenario:

        1. Deploy MOS 9.0 with Murano plugin and murano-node in non-ha
        2. Run OSTF
        3. Apply MU for 9.1
        4. Run OSTF

        """

        self.env.revert_snapshot("deploy_murano_plugin")
        self.apply_maintenance_update_90_to_91()
        self.run_ostf(['sanity', 'smoke', 'tests_platform'])



