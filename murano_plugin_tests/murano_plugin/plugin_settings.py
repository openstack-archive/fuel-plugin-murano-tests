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

from murano_plugin_tests.helpers import helpers
from murano_plugin_tests import settings


name = 'detach-murano'
role_name = ['murano-node']
plugin_path = settings.MURANO_PLUGIN_PATH
version = helpers.get_plugin_version(plugin_path)

glare = True
a_o_o = 'http://storage.apps.openstack.org/'

default_options = {
    'murano_glance_artifacts/value': glare,
    'murano_repo_url/value': a_o_o
}

murano_options = default_options
