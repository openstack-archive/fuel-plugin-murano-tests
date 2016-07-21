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

from fuelweb_test.tests import base_test_case

from murano_plugin_tests.helpers import checkers
from murano_plugin_tests.helpers import helpers
from murano_plugin_tests.helpers import remote_ops
from murano_plugin_tests.murano_plugin import plugin_settings


class MuranoPluginApi(object):
    """Class to manage Murano Detach plugin."""

    def __init__(self):
        self.test = base_test_case.TestBasic()
        self.env = self.test.env
        self.settings = plugin_settings
        self.helpers = helpers.PluginHelper(self.env)
        self.checkers = checkers
        self.remote_ops = remote_ops

    def __getattr__(self, item):
        return getattr(self.test, item)

    @property
    def base_nodes(self):
        """Return a dict mapping nodes to Fuel roles without HA."""
        return {
            'slave-01': ['controller'],
            'slave-02': ['compute', 'cinder'],
            'slave-03': self.settings.role_name,
        }

    @property
    def ha_nodes(self):
        """Return a dict mapping nodes to Fuel roles with HA."""
        return {
            'slave-01': ['controller'],
            'slave-02': ['controller'],
            'slave-03': ['controller'],
            'slave-04': ['compute', 'cinder'],
            'slave-05': ['compute'] + self.settings.role_name,
        }

    def prepare_plugin(self):
        """Upload and install the plugin on the Fuel master node."""
        self.helpers.prepare_plugin(self.settings.plugin_path)

    def run_ostf(self):
        self.helpers.run_ostf(test_sets=['sanity', 'smoke', 'ha',
                                         'tests_platform'])

    def activate_plugin(self, options=None):
        """Enable and configure the plugin in the environment."""
        if options is None:
            options = self.settings.default_options
        self.helpers.activate_plugin(
            self.settings.name, self.settings.version, options)

    def uninstall_plugin(self):
        """Uninstall plugin from Fuel."""
        return self.helpers.uninstall_plugin(self.settings.name,
                                             self.settings.version)
