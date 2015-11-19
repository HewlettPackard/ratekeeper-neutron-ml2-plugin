# (c) Copyright 2015 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from networking_hp.plugins.ml2.drivers.ratekeeper.common import (
    constants as rk_const)
from networking_hp.plugins.ml2.drivers.ratekeeper.ml2 import (
    ratekeeper_ml2_driver as rk_driver)
from neutron.i18n import _LE, _LI, _LW
from oslo_log import log as logging

from neutron.extensions import portbindings
from neutron.plugins.common import constants as plugin_const
from neutron.plugins.ml2.drivers import mech_agent

LOG = logging.getLogger(__name__)

class HpRatekeeperMechanismDriver(mech_agent.SimpleAgentMechanismDriverBase):

    def __init__(self):
        LOG.debug("RK: __init__")
        vif_details = {portbindings.CAP_PORT_FILTER: True,
                       portbindings.OVS_HYBRID_PLUG: True}
        super(HpRatekeeperMechanismDriver, self).__init__(
            rk_const.AGENT_TYPE_RK,
            portbindings.VIF_TYPE_OTHER,
            vif_details)
        self.rk_driver = rk_driver.RkAgentDriver()
        self.rk_driver.initialize()


    def get_allowed_network_types(self, agent):
        return (agent['configurations'].get('tunnel_types', []) +
                [plugin_const.TYPE_LOCAL, plugin_const.TYPE_FLAT,
                 plugin_const.TYPE_VLAN])

    def get_mappings(self, agent):
        return agent['configurations'].get('bridge_mappings', {})

    # SHould this be kept here?
    def create_port_postcommit(self, context):
        self.rk_driver.create_port_postcommit(context)

    def delete_port_precommit(self, context):
        self.rk_driver.delete_port_precommit(context)

    def update_port_postcommit(self, context):
        self.rk_driver.update_port_postcommit(context)

    def delete_network_precommit(self, context):
        self.rk_driver.delete_network_precommit(context)
