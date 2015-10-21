# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# All rights reserved.
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

import eventlet
eventlet.monkey_patch()
from oslo_log import log
from oslo_utils import timeutils

from neutron.common import rpc as common_rpc
from neutron.common import topics
from neutron import context as neutron_context
from neutron.extensions import portbindings
from neutron import manager

from networking_hp.plugins.ml2.drivers.ratekeeper.common import (
    constants as rk_const)
from networking_hp.plugins.ml2.drivers.ratekeeper.db import (
    ratekeeper_db as rk_db)
from networking_hp.plugins.ml2.drivers.ratekeeper.ml2 import (
    ratekeeper_rpc as rk_rpc)

from neutron.i18n import _LE, _LI, _LW

LOG = log.getLogger(__name__)

class RkAgentDriver(object):
    """Ratekeeper Python Driver for Neutron.

    This code is the backend implementation for the Ratekeeper ML2
    MechanismDriver for OpenStack Neutron.
    """

    def initialize(self):
        self.context = neutron_context.get_admin_context()
        self._start_rpc_listeners()
        self._plugin = None
        self._pool = None

    @property
    def plugin(self):
        if self._plugin is None:
            self._plugin = manager.NeutronManager.get_plugin()
        return self._plugin

    @property
    def threadpool(self):
        if self._pool is None:
            self._pool = eventlet.GreenPool(2)
        return self._pool

    def _start_rpc_listeners(self):
        self.notifier = rk_rpc.RkAgentNotifyAPI(topics.AGENT)
        self.endpoints = [rk_rpc.RkServerRpcCallback(self.notifier)]
        self.topic = rk_const.RATEKEEPER
        self.conn = common_rpc.create_connection(new=True)
        self.conn.create_consumer(self.topic, self.endpoints, fanout=False)
        return self.conn.consume_in_threads()

    def _notify_agent(self, context, port_info, host):

        chosen_agent = None
        agents = self.plugin.get_agents(
            self.context,
            filters={'agent_type': [rk_const.AGENT_TYPE_RK]})

        LOG.debug("RK: agents: %s" % agents)
        for agent in agents:
	
            if agent and 'host' in agent:
                host = agent['host']
            else:
                LOG.error(_LE("RK: Failed to find Ratekeeper Agent with host %s" % host))
                return

            try:
                self.notifier.port_update(self.context, port_info, host)
            except Exception:
                LOG.exception(_LE("RK: Failed to notify agent to update port"))

    def create_port_postcommit(self, context):

        LOG.debug("RK: create_port_postcommit. context: %s", context)
        port_id = context._port['id']
        segment_id = context._network_context._segments[0]['segmentation_id']
        rk_db.update_vif_segment_id(port_id, segment_id, context._plugin_context.session)

    def delete_port_precommit(self, context):

        LOG.debug("RK: delete_port_precommit. context: %s", context)
        vif_id = context._port['id']
        rk_db.delete_vif_record(vif_id, context._plugin_context.session)


    def update_port_postcommit(self, context):

        port = context.current
        LOG.debug("RK: update_port_postcommit. Port context: %s", context._port)
        if rk_const.RK_MIN_RATE in port:
	    host = port[portbindings.HOST_ID]
	    port_info = { 
		'port_id': port['id'],
		rk_const.RK_MIN_RATE: port[rk_const.RK_MIN_RATE],
		rk_const.RK_MAX_RATE: port[rk_const.RK_MAX_RATE]
	    }
	    self._notify_agent(context, port_info, host)

    def delete_network_precommit(self, context):

        LOG.debug("RK: delete_network_precommit. context: %s", context)

        network_id = context._network['id']
        rk_db.delete_vnet_record(network_id, context._plugin_context.session)
