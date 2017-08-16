# Copyright (c) 2017 Red Hat
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import ast

from novajoin_tempest_plugin.tests.scenario import novajoin_manager
from oslo_log import log as logging
from tempest import config

CONF = config.CONF
LOG = logging.getLogger(__name__)

DOMAIN = 'tripleodomain.example.com'
REALM = 'TRIPLEODOMAIN.EXAMPLE.COM'

HOSTS = [
    'undercloud',
    'overcloud-controller-0'
]

CONTROLLER_CERT_TAGS = [
    'mysql',
    'rabbitmq',
    'httpd-ctlplane',
    'httpd-internal_api',
    'httpd-storage',
    'httpd-storage_mgmt',
    'haproxy-ctlplane-cert',
    'haproxy-external-cert',
    'haproxy-internal_api-cert',
    'haproxy-storage-cert',
    'haproxy-storage_mgmt-cert'
]

CONTROLLERS = ['overcloud-controller-0']


class TripleOTest(novajoin_manager.NovajoinScenarioTest):

    """The test suite for tripleO configuration

    Novajoin is currently deployed in tripleO as part of the
    undercloud as part of a tripleO deployment.

    This test is to validate that all the nodes and services
    for an HA deployment have been correctly created.

    This means:
         * Validating that the undercloud is enrolled in IPA
         * Validating that the controller is enrolled in IPA
         * Validating that the compute node is enrolled
         * Validating that HA services have been created in IPA
         * Validating that certs are being tracked.
         * Validate that TLS connections are being established for
           all internal services
    """

    @classmethod
    def skip_checks(cls):
        super(TripleOTest, cls).skip_checks()
        pass

    def _get_server_id(self, name):
        # params = {'name': name}
        params = {'all_tenants': '', 'name': name}
        resp = self.servers_client.list_servers(detail=True, **params)
        print(resp)
        links = resp['servers'][0]['links']
        for link in links:
            if link['rel'] == 'self':
                href = link['href']
                return href.split('/')[-1]
        return None

    def test_hosts_are_registered(self):
        for host in HOSTS:
            hostname = "{host}.{domain}".format(host=host, domain=DOMAIN)
            self.verify_host_registered_with_ipa(hostname)
            self.verify_host_has_keytab(hostname)

    def test_verify_compact_services_created(self):
        for host in CONTROLLERS:
            metadata = self.servers_client.list_server_metadata(
                self._get_server_id(host))['metadata']
            services = metadata['compact_services']
            compact_services = ast.literal_eval(services)
            print(compact_services)
            self.verify_compact_services(
                services=compact_services,
                host=host,
                realm=REALM,
                domain=DOMAIN,
                verify_certs=True
            )

    def test_verify_controller_managed_services(self):
        for host in CONTROLLERS:
            metadata = self.servers_client.list_server_metadata(
                self._get_server_id(host))['metadata']
            managed_services = [metadata[key] for key in metadata.keys()
                                if key.startswith('managed_service_')]
            print(managed_services)
            self.verify_managed_services(
                services=managed_services,
                realm=REALM,
                domain=DOMAIN,
                verify_certs=True)

    def test_verify_service_certs_are_tracked(self):
        # TODO(alee) get correct overcloud_ip
        for host in CONTROLLERS:
            server_id = self._get_server_id(host)
            print(self.get_server_ip(server_id))

        overcloud_ip = '192.168.24.17'
        for tag in CONTROLLER_CERT_TAGS:
            self.verify_overcloud_cert_tracked(
                overcloud_ip,
                'heat-admin',
                tag
            )

    def test_overcloud_is_ipaclient(self):
        # TODO(alee) get correct overcloud_ip
        overcloud_ip = '192.168.24.17'
        self.verify_overcloud_host_is_ipaclient(
            overcloud_ip,
            'heat-admin'
        )
