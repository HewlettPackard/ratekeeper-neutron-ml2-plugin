# Copyright 2015 Cisco Systems, Inc.
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

"""Extensions Driver for HP Ratekeeper."""

from oslo_config import cfg
from oslo_log import log

from networking_hp.plugins.ml2.drivers.ratekeeper.common import (
    config as rk_cfg)
from networking_hp.plugins.ml2.drivers.ratekeeper.common import (
    constants as rk_const)
from networking_hp.plugins.ml2.drivers.ratekeeper.db import (
    ratekeeper_db as rk_db)
from networking_hp.plugins.ml2.drivers.ratekeeper.ml2 import (
    extensions as rk_extensions)

from neutron.api import extensions as extensions_api
from neutron.api.v2 import attributes
from neutron.plugins.ml2.common import exceptions as ml2_exc
from neutron.plugins.ml2 import driver_api as api
from neutron.i18n import _LE

LOG = log.getLogger(__name__)

rk_cfg.register_agent_opts()

class HpRatekeeperExtensionDriver(api.ExtensionDriver):
    """HP Ratekeeper ML2 Extension Driver."""

    # List of supported extensions for hp Ratekeeper.
    _supported_extension_alias = 'ratekeeper'

    def initialize(self):
        extensions_api.append_api_extensions_path(rk_extensions.__path__)

    @property
    def extension_alias(self):
        """
        Supported extension alias.

        :returns: alias identifying the core API extension supported
                  by this driver
        """
        return self._supported_extension_alias


    def _validate_rates(self, min_attr, max_attr):

	if min_attr > max_attr:
	   min_attr = max_attr;

	return (min_attr, max_attr)

    def process_create_network(self, context, data, result):
        """Implementation of abstract method from ExtensionDriver class."""
	LOG.debug("RK: process_create_network(). data: %s", data)

        net_id = result.get('id')
	port_min_attr = data.get(rk_const.RK_MIN_RATE)
	port_max_attr = data.get(rk_const.RK_MAX_RATE)

        if not attributes.is_attr_set(port_min_attr) or \
                not attributes.is_attr_set(port_max_attr):
            port_min_attr = cfg.CONF.RATEKEEPER.default_min_rate
            port_max_attr = cfg.CONF.RATEKEEPER.default_max_rate

	port_min_attr, port_max_attr = self._validate_rates(port_min_attr, port_max_attr)

	LOG.debug("RK: port_min_attr %s, port_max_attr %s", port_min_attr, port_max_attr)

        with context.session.begin(subtransactions=True):
            try:
                rk_db.create_vnet_record(net_id, port_min_attr, port_max_attr, context.session)
	    except Exception as e:
		LOG.error(_LE("RK: error %s" % e))
                raise ml2_exc.MechanismDriverError()

	result[rk_const.RK_MIN_RATE] = port_min_attr
	result[rk_const.RK_MAX_RATE] = port_max_attr

    def process_update_network(self, context, data, result):
        """Implementation of abstract method from ExtensionDriver class."""
    	LOG.debug("RK: process_update_network().  data: %s" , data)

        net_id = result.get('id')
	net_min_attr = data.get(rk_const.RK_MIN_RATE)
	net_max_attr = data.get(rk_const.RK_MAX_RATE)

    	LOG.debug("RK: update_network: %s and %s", net_min_attr, net_max_attr)
        if attributes.is_attr_set(net_min_attr) and \
               attributes.is_attr_set(net_max_attr):

            with context.session.begin(subtransactions=True):
                try:
                    res = rk_db.get_vnet_profile(net_id, context.session)

		    if res:
           	        rk_db.update_vnet_rate_limit(net_id, net_min_attr, net_max_attr, context.session)

		    else:
                        # Network not found and can't be updated.  Create instead
		        try:
                    	    rk_db.create_vnet_record(net_id, net_min_attr, net_max_attr, context.session)
            	        except Exception as e:
                	    LOG.error(_LE("RK: update_network: error %s" % e)) 
                	    raise ml2_exc.MechanismDriverError()

    		    LOG.debug("RK: update_network: res: %s", res)

		except Exception as a:
                    LOG.error(_LE("RK: update_network: error %s" % a))
                    raise ml2_exc.MechanismDriverError()


    def extend_network_dict(self, session, model, result):
        """Implementation of abstract method from ExtensionDriver class."""
	LOG.debug("RK: extend_network_dict(). result: %s", result)

        net_id = result.get('id')
        with session.begin(subtransactions=True):
            try:
                res = rk_db.get_vnet_profile(net_id, session)
                result[rk_const.RK_MIN_RATE] = res.min_rate
                result[rk_const.RK_MAX_RATE] = res.max_rate
            except Exception as e:
                # Do nothing if the net is not found.
		LOG.debug(_LE("RK: do nothing... net not found: %s" % e))


    def process_create_port(self, context, data, result):
        """Implementation of abstract method from ExtensionDriver class."""
	LOG.debug("RK: process_create_port(). data: %s", data)

        port_id = result.get('id')
	port_min_attr = data.get(rk_const.RK_MIN_RATE)
	port_max_attr = data.get(rk_const.RK_MAX_RATE)

        if not attributes.is_attr_set(port_min_attr) or \
        	not attributes.is_attr_set(port_max_attr):

	    # check network defaults
	    network_id = result.get('network_id')
            with context.session.begin(subtransactions=True):
                try:
                    LOG.debug("RK: no limits on port... look for network_id: %s", network_id)
                    res = rk_db.get_vnet_profile(network_id, context.session)
		    net_min_attr, net_max_attr = res.min_rate, res.max_rate

		    if not attributes.is_attr_set(port_min_attr):
			port_min_attr = net_min_attr
		    if not attributes.is_attr_set(port_max_attr):
			port_max_attr = net_max_attr

		    port_min_attr, port_max_attr = self._validate_rates(
			port_min_attr, port_max_attr)

            	except Exception as e:
                    # Do nothing if the port is not found.
		    LOG.debug("RK: do nothing... port not found: %s" % e)
                    return


	LOG.debug("RK: port_min_attr %s, port_max_attr %s", port_min_attr, port_max_attr)

        with context.session.begin(subtransactions=True):
            try:
	        network_id = -1
                rk_db.create_vif_record(port_id, network_id, port_min_attr, 
					port_max_attr, context.session)
	    except Exception as e:
		LOG.error(_LE("RK: error %s" % e))
                raise ml2_exc.MechanismDriverError()

	result[rk_const.RK_MIN_RATE] = port_min_attr
	result[rk_const.RK_MAX_RATE] = port_max_attr

    def process_update_port(self, context, data, result):
        """Implementation of abstract method from ExtensionDriver class."""
    	LOG.debug("RK: process_update_port(). data: %s", data)

        port_id = result.get('id')
	port_min_attr = data.get(rk_const.RK_MIN_RATE)
	port_max_attr = data.get(rk_const.RK_MAX_RATE)
        with context.session.begin(subtransactions=True):
            try:
                res = rk_db.get_vif_profile(port_id, context.session)
		port_min_attr = res.min_rate if not port_min_attr else port_min_attr
		port_max_attr = res.max_rate if not port_max_attr else port_max_attr

           	rk_db.update_vif_rate_limit(port_id, port_min_attr, 
						port_max_attr, context.session)

            except Exception as e:
                # Do nothing if the port is not found.
		LOG.debug("RK: do nothing... port not found: %s", e)

    def extend_port_dict(self, session, model, result):
        """Implementation of abstract method from ExtensionDriver class."""
	LOG.debug("RK: extend_port_dict()")

        port_id = result.get('id')
        with session.begin(subtransactions=True):
            try:
                res = rk_db.get_vif_profile(port_id, session)
                result[rk_const.RK_MIN_RATE] = res.min_rate
                result[rk_const.RK_MAX_RATE] = res.max_rate
            except Exception as e:
                # Do nothing if the port is not found.
		LOG.debug("RK: do nothing... port not found: %s" % e)

	LOG.debug("RK: extended result: %s", result)
