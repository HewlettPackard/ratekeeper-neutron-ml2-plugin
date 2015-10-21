# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
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

from oslo_log import log as logging
from nova.i18n import _LE
from oslo_config import cfg

from nova.compute.resources import base
from networking_hp.plugins.ml2.drivers.ratekeeper.common import (
    constants as rk_const)

LOG = logging.getLogger(__name__)


class PORTSPEED(base.Resource):
    """PORTSPEED compute resource plugin.
    """
    def __init__(self):
        LOG.debug('RK: __init__')
        # initialize to a 'zero' resource.
        # reset will be called to set real resource values
        self._total_bandwidth = 0
        self._reserved_bandwidth = 0
        self._instances = {}

    def reset(self, resources, driver):
        LOG.debug('RK: reset')
        #self._total_bandwidth = cfg.CONF.GATEKEEPER.port_speed_mbps
        self._total_bandwidth = 10000
        self._reserved_bandwidth = 0

    def test(self, usage, limits):
        LOG.error(_LE('RK: test'))

    def add_instance(self, usage):
        LOG.debug('RK: add_instance: usage: %s' % usage)
	flavor = usage.get('flavor', {})
        extra_specs = flavor.get('extra_specs', {})
        instance_id = usage.get('uuid', '')

        requested = int(extra_specs.get(rk_const.RK_MIN_RATE, 0))
        if instance_id in self._instances:
            requested = self._instances[instance_id]
        
        self._reserved_bandwidth += requested 
        self._instances[instance_id] = requested
        LOG.debug('RK: requested min_rate %s, reserved_bandwidth %s' % (requested, self._reserved_bandwidth))

    def remove_instance(self, usage):
        LOG.debug('RK: remove_instance: usage: %s ' % usage)
        instance_id = usage.get('uuid', '')
	if instance_id in self._instances:
            requested = self._instances[instance_id]
            del self._instances[instance_id]
            self._reserved_bandwidth -= requested

    def write(self, resources):
        resources['stats']['port_speed_mbps'] = self._total_bandwidth
        resources['stats']['reserved_bandwidth_mbps'] = self._reserved_bandwidth
        LOG.debug('RK: write resources: %s' % resources)

    def report_free(self):
        free_bandwidth = self._total_bandwidth - self._reserved_bandwidth
        LOG.debug('Free bandwidth: %s' % free_bandwidth)
