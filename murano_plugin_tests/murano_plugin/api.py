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

import functools

from devops.helpers import helpers as devops_helpers
from fuelweb_test.helpers.decorators import retry
from fuelweb_test import logger
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
    def only_controllers_ha(self):
        """Return a dict mapping nodes to Fuel roles with HA."""
        return {
            'slave-01': ['controller'],
            'slave-02': ['controller'],
            'slave-03': ['controller'],
            'slave-04': ['compute', 'cinder']
        }

    @property
    def only_controllers(self):
        """Return a dict mapping nodes to Fuel roles non-HA."""
        return {
            'slave-01': ['controller'],
            'slave-02': ['compute', 'cinder']
        }

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

    @property
    def full_ha_nodes(self):
        """Return a dict mapping nodes to Fuel roles with full HA."""
        return {
            'slave-01': ['controller'],
            'slave-02': ['controller'],
            'slave-03': ['controller'],
            'slave-04': ['compute', 'cinder'],
            'slave-05': ['compute', 'cinder'],
            'slave-06': ['compute', 'cinder'],
            'slave-07': self.settings.role_name,
            'slave-08': self.settings.role_name,
            'slave-09': self.settings.role_name,
        }

    def prepare_plugin(self):
        """Upload and install the plugin on the Fuel master node."""
        self.helpers.prepare_plugin(self.settings.plugin_path)

    def run_ostf(self, test_sets):
        self.helpers.run_ostf(test_sets=test_sets)

    def activate_plugin(self, options=None):
        """Enable and configure the plugin in the environment."""
        if options is None:
            options = self.settings.default_options
        self.helpers.activate_plugin(
            self.settings.name, self.settings.version, options)

    @retry(count=3, delay=120)
    def check_plugin_online(self):
        """Checks that plugin is working. Runs platform Murano OSTF."""
        test_name = ('fuel_health.tests.tests_platform.test_murano_linux.'
                     'MuranoDeployLinuxServicesTests.'
                     'test_deploy_dummy_app_with_glare')
        self.helpers.run_single_ostf(test_sets=['tests_platform'],
                                     test_name=test_name,
                                     timeout=60 * 20)

    def check_plugin_sanity(self):
        """Checks that plugin is working. Runs sanity Murano OSTF."""
        test_name = ('fuel_health.tests.sanity.test_sanity_murano.'
                     'MuranoSanityTests.'
                     'test_create_and_delete_service')

        self.helpers.run_single_ostf(test_sets=['tests_platform'],
                                     test_name=test_name,
                                     timeout=5 * 10)

    def uninstall_plugin(self):
        """Uninstall plugin from Fuel."""
        return self.helpers.uninstall_plugin(self.settings.name,
                                             self.settings.version)

    def check_uninstall_failure(self):
        return self.helpers.check_plugin_cannot_be_uninstalled(
            self.settings.name, self.settings.version)

    def wait_plugin_online(self, timeout=5 * 120):
        """Wait until the plugin will start working properly.
        """

        def check_availability():
            try:
                self.check_plugin_sanity()
                return True
            except AssertionError:
                return False

        logger.info('Wait a plugin become online')
        msg = "Plugin has not become online after a waiting period"
        devops_helpers.wait(
            check_availability, interval=30, timeout=timeout, timeout_msg=msg)

    def check_plugin_failover(self, operation, role_name):
        fuel_web_client = self.helpers.fuel_web
        operations = {
            "soft_reboot": fuel_web_client.warm_restart_nodes,
            "hard_reboot": functools.partial(
                fuel_web_client.cold_restart_nodes, wait_offline=False)
        }
        nailgun_nodes = fuel_web_client.get_nailgun_cluster_nodes_by_roles(
            self.helpers.cluster_id, role_name)
        target_node = fuel_web_client.get_devops_nodes_by_nailgun_nodes(
            nailgun_nodes[:1])
        operations[operation](target_node)
        self.helpers.wait_os_cluster_readiness()

    def apply_maintenance_update(self):
        """Method applies maintenance updates on whole cluster
        from MOS 9.0 to MOS 9.x

        1) Add latest proposed repository
        2) Import PGP key for installed repository
        3) Install `python-cudet`
        4) Add repository and deploy changes
        5) Update with keys all nodes
        6) Update-prepare prepare master
        7) Update-prepare update master
        8) Update-prepare prepare env
        9) Update
        10) Verify that you have the latest packages included in
        Mirantis OpenStack 9.1 -  Potential updates: ALL NODES UP-TO-DATE

        """
        self.helpers.add_update_repo()

        logger.info("Install python-cudet library")

        self.helpers.install_python_cudet()

        logger.info("Update-prepare prepare master and "
                    "Update-prepare update master")

        self.helpers.prepare_update_master_node()

        logger.info("Update-prepare prepare env")

        self.helpers.prepare_for_update()

        logger.info("Install MU")

        self.helpers.install_mu()

        self.helpers.check_update()
