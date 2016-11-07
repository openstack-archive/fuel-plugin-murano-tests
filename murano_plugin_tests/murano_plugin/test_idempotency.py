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
class TestMuranoPuppetIdempotency(api.MuranoPluginApi):
    """Class for testing puppet idempotency for Murano plugin."""

    @test(depends_on_groups=["deploy_murano_plugin_on_controller"],
          groups=["check_plugin_idempotency_on_controller", "deploy",
                  "murano", "idempotency", "failover"])
    @log_snapshot_after_test
    def check_plugin_idempotency_on_controller(self):
        """Rerun puppet apply on controller and check plugin idempotency.

        Scenario:
            1. Revert snapshot with deployed cluster (controller + compute)
            2. Run puppet apply for controller

        Duration 10m
        """

        self.env.revert_snapshot("deploy_murano_plugin_on_controller")

        plugin_path = '/etc/fuel/plugins/detach-murano-1.0/'
        modules_path = plugin_path + 'modules:/etc/puppet/modules/'
        plugin_manifest_path = plugin_path + 'manifests/'

        cluster_id = self.fuel_web.get_last_created_cluster()
        attr = self.fuel_web.client.get_cluster_attributes(cluster_id)
        cfapi = attr['editable']['detach-murano']['metadata']['versions'][0][
            'murano_cfapi']

        contr_node = self.fuel_web.get_nailgun_node_by_name('slave-01')

        list_controller_manifests = ['murano_hiera_override.pp',
                                     'pin_murano_plugin_repo.pp',
                                     'murano.pp',
                                     'murano_rabbitmq.pp',
                                     'murano_keystone.pp',
                                     'murano_db.pp',
                                     'murano_dashboard.pp'
                                     'import_murano_package.pp',
                                     'murano_logging.pp',
                                     'update_openrc.pp',
                                     'murano_haproxy.pp']
        if cfapi['value']:
            list_controller_manifests.insert(4, 'murano_cfapi.pp')

        for manifest in list_controller_manifests:
            cmd = 'puppet apply --modulepath={0} {1} {2}'.format(
                modules_path, plugin_manifest_path + manifest, '-d --test')
            self.ssh_manager.check_call(ip=contr_node['ip'],
                                        command=cmd,
                                        expected=[0])

    @test(depends_on_groups=["deploy_murano_plugin"],
          groups=["check_plugin_idempotency_on_murano_node", "deploy",
                  "murano", "idempotency", "failover"])
    @log_snapshot_after_test
    def check_plugin_idempotency_on_murano_node(self):
        """Rerun puppet apply on murano node and check plugin idempotency.

        Scenario:
            1. Revert snapshot with deployed cluster
            2. Run puppet apply for murano node

        Duration 10m
        """

        self.env.revert_snapshot("deploy_murano_plugin")

        plugin_path = '/etc/fuel/plugins/detach-murano-1.0/'
        modules_path = plugin_path + 'modules:/etc/puppet/modules/'
        plugin_manifest_path = plugin_path + 'manifests/'
        ssl_path = '/etc/puppet/modules/osnailyfacter/modular/ssl/'

        cluster_id = self.fuel_web.get_last_created_cluster()
        attr = self.fuel_web.client.get_cluster_attributes(cluster_id)
        cfapi = attr['editable']['detach-murano']['metadata']['versions'][0][
            'murano_cfapi']

        murano_node = self.fuel_web.get_nailgun_node_by_name('slave-03')

        list_murano_manifests = ['murano_hiera_override.pp',
                                 'pin_murano_plugin_repo.pp',
                                 'murano.pp',
                                 'murano_rabbitmq.pp',
                                 'import_murano_package.pp',
                                 'murano_logging.pp']
        if cfapi['value']:
            list_murano_manifests.insert(4, 'murano_cfapi.pp')

        list_ssl_manifests = ['ssl_keys_saving.pp',
                              'ssl_add_trust_chain.pp',
                              'ssl_dns_setup.pp']

        for manifest in list_murano_manifests:
            cmd = 'puppet apply --modulepath={0} {1} {2}'.format(
                modules_path, plugin_manifest_path + manifest, '-d --test')
            self.ssh_manager.check_call(ip=murano_node['ip'],
                                        command=cmd,
                                        expected=[0])

        for manifest in list_ssl_manifests:
            cmd = 'puppet apply --modulepath={0} {1} {2}'.format(
                modules_path, ssl_path + manifest, '-d --test')
            self.ssh_manager.check_call(ip=murano_node['ip'],
                                        command=cmd,
                                        expected=[0])
