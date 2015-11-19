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

from nova.scheduler import filters
from oslo_config import cfg
from oslo_log import log as logging
from nova.i18n import _LW
from nova import context
from nova import objects

from networking_hp.plugins.ml2.drivers.ratekeeper.common import (
    constants as rk_const)

LOG = logging.getLogger(__name__)

class PortSpeedFilter(filters.BaseHostFilter):
    """NOOP host filter. Returns all hosts."""

    # list of hosts doesn't change within a request
    run_filter_once_per_request = True
    compute_nodes = {}

    def __init__(self):
        LOG.debug("RK: Ratekeeper filter initialized")

    def host_passes(self, host_state, filter_properties):
        """Only return hosts with sufficient network bandwidth."""

        request_spec = filter_properties.get('request_spec', {})
        instance = request_spec.get('instance_properties', {})
        flavor = instance.get('flavor', {})
        extra_specs = flavor.get('extra_specs', {})
        LOG.debug('RK: extra_specs: %s' % extra_specs)
        requested_min_rate = int(extra_specs.get(rk_const.RK_MIN_RATE, 0))

        compute = self.get_compute_node(host_state.hypervisor_hostname)
        if compute:
            port_speed = int(compute.stats.get('port_speed_mbps', 0))
            reserved_bandwidth = int(compute.stats.get('reserved_bandwidth_mbps', 0))

            #max_bandwidth = port_speed * CONF.port_speed_allocation_ratio
            max_bandwidth = port_speed
            avail_bandwidth = max_bandwidth - reserved_bandwidth

            LOG.info('RK: Doing port speed filter for host = %s. '
                 'Port Speed = %d '
                 'Maximum bandwidth = %d '
                 'Reserved bandwidth = %d '
                 'Available bandwidth = %d '
                 'Minimum rate requested = %d' %
                 (host_state.host, port_speed, max_bandwidth,
                 reserved_bandwidth, avail_bandwidth,
                 requested_min_rate))

            if requested_min_rate > avail_bandwidth:
                LOG.info(_("RK: %(host_state)s does not have %(requested_min_rate) mbps "
                    "available bandwidth , it only has %(avail_bandwidth) mbps available."),
                    locals())
                return False

            LOG.info('RK: %s complied with minimum port speed' % host_state.host)
            # save oversubscription limit for compute node to test against:
            #host_state.limits['port_speed'] = max_bandwidth

        return True


    def get_compute_node(self, hypervisor_hostname):

        admin = context.get_admin_context()
        computes = objects.ComputeNodeList.get_by_hypervisor(admin, hypervisor_hostname)
        #computes = objects.ComputeNodeList.get_all(admin)
	if len(computes) != 1:
            LOG.warning(_LW('RK: compute node not found: %s' % hypervisor_hostname))
            return None
        return computes[0]
