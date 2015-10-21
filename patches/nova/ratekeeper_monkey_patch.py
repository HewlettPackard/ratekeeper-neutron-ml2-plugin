# Copyright (c) 2012 OpenStack Foundation
# All Rights Reserved.
# Copyright 2013 Red Hat, Inc.
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

"""Decorator to monkey patch nova --specifically the function 
nova.network.neutronv2.api._populate_neutron_extension_values--
to enable passing to neutron at port creation time the rk_rates
specified by the image flavor 
"""

from oslo_log import log
from networking_hp.plugins.ml2.drivers.ratekeeper.common import (
    constants as rk_const)

LOG = log.getLogger(__name__)

def ratekeeper_decorator(name, fn):
    """Decorator for notify which is used from utils.monkey_patch().

        :param name: name of the function
        :param fn: - object of the function
        :returns: fn -- decorated function

    """
    def wrapped_func(*args, **kwarg):

        if fn.func_name == '_populate_neutron_extension_values':
            LOG.debug("RK: wrapping function call: %s" % fn.func_name)
            foo, context, instance, pci_request_id, port_req_body = args
            flavor = instance.get_flavor()
            extra_specs = flavor.get('extra_specs', {})
            min_rate = int(extra_specs.get(rk_const.RK_MIN_RATE, 0))
            max_rate = int(extra_specs.get(rk_const.RK_MAX_RATE, 0))
            port_req_body['port'][rk_const.RK_MIN_RATE] = min_rate
            port_req_body['port'][rk_const.RK_MAX_RATE] = max_rate
            ret = fn(*args, **kwarg)
            LOG.debug("RK: Extended neutron request: %s" % args[4])
            return ret

        return fn(*args, **kwarg)

    return wrapped_func


