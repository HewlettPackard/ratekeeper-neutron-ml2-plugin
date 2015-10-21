# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
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

import time

from oslo_log import log
import oslo_messaging
from sqlalchemy.orm import exc as sa_exc

from networking_hp.plugins.ml2.drivers.ratekeeper.common import (
    constants as rk_const)
from networking_hp.plugins.ml2.drivers.ratekeeper.db import (
    ratekeeper_db as rk_db)

from neutron.common import exceptions as exc
from neutron.common import rpc as common_rpc
from neutron.common import topics
from neutron.db import models_v2
from neutron.extensions import portbindings
from neutron import manager
from neutron.plugins.ml2 import driver_api as api
from neutron.plugins.ml2 import driver_context
from neutron.i18n import _, _LW, _LE, _LI

LOG = log.getLogger(__name__)


class RkServerRpcCallback(object):

    """Plugin side of the HP Ratekeeper rpc.

    This class contains extra rpc callbacks to be served for use by the
    Ratekeeper Agent.
    """
    target = oslo_messaging.Target(version='1.0')

    def __init__(self, notifier=None):
        super(RkServerRpcCallback, self).__init__()
        self.notifier = notifier

    @property
    def plugin(self):
        return manager.NeutronManager.get_plugin()

    def get_port_rates(self, rpc_context, **kwargs):
        """RPC for getting port rate info.

        This method provides information about the ratekeeper rates 
        a given port.
        """
	result = {}
        port_id = kwargs.get('port_id')
        LOG.debug("RK: get_port_rates_list: %s", port_id)

        try:
            res = rk_db.get_vif_profile(port_id)
	    result = { rk_const.RK_MIN_RATE:res.min_rate, 
			rk_const.RK_MAX_RATE:res.max_rate }

        except Exception as e:
            # Do nothing if the port is not found.
            LOG.debug("RK: do nothing... port not found: %s", e)

	return result


class RkAgentNotifyAPI(object):

    """Agent side of the Ratekeeper rpc API."""

    def __init__(self, topic=topics.AGENT):
        target = oslo_messaging.Target(topic=topic, version='1.0')
        self.client = common_rpc.get_client(target)
        self.topic = topic

    def _get_rk_port_topic(self, action):
        return topics.get_topic_name(self.topic,
                                     rk_const.RK_PORT,
                                     action)

    def port_update(self, context, port_info, host):
        cctxt = self.client.prepare(
            topic=self._get_rk_port_topic(topics.UPDATE))
        return cctxt.call(context, 'port_update',
                          port_info=port_info, host=host)
