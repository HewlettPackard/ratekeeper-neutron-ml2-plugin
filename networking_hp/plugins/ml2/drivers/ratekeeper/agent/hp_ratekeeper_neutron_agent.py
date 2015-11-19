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

import os
import copy
import signal
import sys
import time

import eventlet
eventlet.monkey_patch()

import oslo_messaging

from oslo_config import cfg
from oslo_log import log as logging

from neutron.agent.common import config as agent_common_config
from neutron.agent import rpc as agent_rpc
from neutron.common import rpc as common_rpc
from neutron.common import constants as common_const
from neutron.common import topics
from neutron.common import config as common_config
from neutron import context
from neutron.i18n import _, _LW, _LE, _LI
from oslo_service import loopingcall
from neutron.agent.linux import utils

from networking_hp.plugins.ml2.drivers.ratekeeper.common import (
    constants as rk_const)


LOG = logging.getLogger(__name__)

# NOTE(toabctl): Don't use /sys/devices/virtual/net here because not all tap
# devices are listed here (i.e. when using Xen)
BRIDGE_FS = "/sys/class/net/"

class RpcPluginApi(agent_rpc.PluginApi):

    def __init__(self, topic):
	super(RpcPluginApi, self).__init__(topic=topic)

class RkPluginApi(agent_rpc.PluginApi):

    def __init__(self, topic):
        target = oslo_messaging.Target(topic=topic, version='1.0')
        self.client = common_rpc.get_client(target)

    def get_port_rates(self, context, port_id, agent_id):
        cctxt = self.client.prepare()
        LOG.info(_("RK: RPC get_ports_rates is called with port_id: %s."),
                 port_id)
        return cctxt.call(context, 'get_port_rates', port_id=port_id,
                          agent_id=agent_id)

class HpRatekeeperNeutronAgent(object):
    """Ratekeeper Neutron Agent 

    This agent receives updates from neutron and calls rkconfing to 
    communicate with teh ratekeeper user module.
    """

    def __init__(self, polling_interval, rk_interface):
	self.polling_interval = polling_interval
	self.rk_intf = rk_interface
        self.agent_state = {
		'binary': 'neutron-hp-ratekeeper-agent',
                'host': cfg.CONF.host,
                'topic': common_const.L2_AGENT_TOPIC,
                'configurations': {}, 
		'agent_type': rk_const.AGENT_TYPE_RK,
                'start_flag': True}
        self.setup_rpc()

        # A list of tap devices
        self.updated_devices = set()

        # A map of device details
	self.device_details = dict()

        # Initialize iteration counter
	self.run_daemon_loop = True


    def setup_rpc(self):
        """Registers the RPC consumers for the plugin."""
        self.agent_id = 'rk-agent-%s' % cfg.CONF.host
        self.topic = topics.AGENT
        self.plugin_rpc = RpcPluginApi(topics.PLUGIN)
        self.state_rpc = agent_rpc.PluginReportStateAPI(topics.PLUGIN)
        self.rk_rpc = RkPluginApi(rk_const.RATEKEEPER)

        # RPC network init.
        self.context = context.get_admin_context_without_session()
        # Handle updates from service.
        self.endpoints = [RkRpcCallbacks(self.context, self)]
        # Define the listening consumers for the agent.  
        consumers = [[rk_const.RK_PORT, topics.UPDATE]] #topics.PORT

	self.use_call = True
        self.connection = agent_rpc.create_consumers(self.endpoints,
                                                     self.topic,
                                                     consumers)

	self.setup_report_states()

        LOG.debug("Finished Setup RPC.")

    def _report_state(self):
        """Reporting agent state to neutron server."""

        try: 
            self.state_rpc.report_state(self.context,
                                        self.agent_state,
                                        self.use_call)
            self.use_call = False
            self.agent_state.pop('start_flag', None)
        except Exception:
            LOG.exception(_("Heartbeat failure - Failed reporting state!"))

    def setup_report_states(self):
        """Method to send heartbeats to the neutron server."""

	report_interval = cfg.CONF.AGENT.report_interval
        if report_interval:
            heartbeat = loopingcall.FixedIntervalLoopingCall(
                self._report_state)
            heartbeat.start(interval=report_interval)
        else:
            LOG.warn(_("Report interval is not initialized."
                       "Unable to send heartbeats to Neutron Server."))

    def get_tap_devices(self):
        devices = set()
        for device in os.listdir(BRIDGE_FS):
            if device.startswith(common_const.TAP_DEVICE_PREFIX):
                devices.add(device)
        return devices

    def scan_devices(self, previous, sync):
        device_info = {}

        # Save and reinitialise the set variable that the port_update RPC uses.
        # This should be thread-safe as the greenthread should not yield
        # between these two statements.
        updated_devices = self.updated_devices
        self.updated_devices = set()

        current_devices = self.get_tap_devices()
        device_info['current'] = current_devices

        if previous is None:
            # This is the first iteration of daemon_loop().
            previous = {'added': set(),
                        'current': set(),
                        'updated': set(),
                        'removed': set()}

        if sync:
            # This is the first iteration, or the previous one had a problem.
            # Re-add all existing devices.
            device_info['added'] = current_devices

            # Retry cleaning devices that may not have been cleaned properly.
            # And clean any that disappeared since the previous iteration.
            device_info['removed'] = (previous['removed'] | previous['current']
                                      - current_devices)

            # Retry updating devices that may not have been updated properly.
            # And any that were updated since the previous iteration.
            # Only update devices that currently exist.
            device_info['updated'] = (previous['updated'] | updated_devices
                                      & current_devices)
        else:
            device_info['added'] = current_devices - previous['current']
            device_info['removed'] = previous['current'] - current_devices
            device_info['updated'] = updated_devices & current_devices

        LOG.debug("RK: device_info: %s", device_info)
        return device_info

    def _device_info_has_changes(self, device_info):
        return (device_info.get('added')
                or device_info.get('updated')
                or device_info.get('removed'))

    def process_network_devices(self, device_info):
        resync_a = False
        resync_b = False

        # Updated devices are processed the same as new ones, as their
        # admin_state_up may have changed. The set union prevents duplicating
        # work when a device is new and updated in the same polling iteration.
        devices_added_updated = (set(device_info.get('added'))
                                 | set(device_info.get('updated')))
        if devices_added_updated:
            resync_a = self.treat_devices_added_updated(devices_added_updated)

        if device_info.get('removed'):
            resync_b = self.treat_devices_removed(device_info['removed'])
        # If one of the above operations fails => resync with plugin
        return (resync_a | resync_b)

    def treat_devices_added_updated(self, devices):
        LOG.debug("RK: treat_devices_added_updated")

        try:
            devices_details_list = self.plugin_rpc.get_devices_details_list(
                self.context, devices, self.agent_id)
        except Exception as e:
            LOG.debug("Unable to get port details for "
                      "%(devices)s: %(e)s",
                      {'devices': devices, 'e': e})
            # resync is needed
            return True

        LOG.debug("RK: devices_details_list: %s", devices_details_list)

        for device_details in devices_details_list:
            device = device_details['device']
            LOG.debug("Port %s added", device)

            if 'port_id' in device_details:

                LOG.info(_LI("Port %(device)s updated. Details: %(details)s"),
                         {'device': device, 'details': device_details})
		port_id = device_details['port_id']
           
		rk_rates = self.rk_rpc.get_port_rates(self.context, port_id, self.agent_id)
                LOG.debug("RK: rk_rates: %s", rk_rates)
		if rk_const.RK_MIN_RATE in rk_rates:

                    vnet_id = device_details['segmentation_id']
		    port_name = device_details['device']
                    utils.execute(["rkconfig", "set",
                           port_name,                        # VNIC
                           "%s.%s" % (self.rk_intf, vnet_id),# TNIC
                           rk_rates[rk_const.RK_MIN_RATE],   # MIN
                           rk_rates[rk_const.RK_MIN_RATE],   # MAX
                           str(vnet_id)],                    # VNET_ID
                           check_exit_code=False)

		    self.device_details[port_name] = [ "%s.%s" % (self.rk_intf, vnet_id),
							str(vnet_id) ]


        return False


    def treat_devices_removed(self, devices):
        LOG.debug("treat_devices_removed: %s", devices)
        resync = False
        for device in devices:
            LOG.info(_LI("Attachment %s removed"), device)
            details = None
            try:

                port_name = device
		tnic, vnet_id = self.device_details[port_name]

                utils.execute(["rkconfig", "set",
                       port_name,               # VNIC
                       tnic,			# TNIC
                       str(-1), 		# MIN
                       str(-1), 		# MAX
                       str(vnet_id)],           # VNET_ID
                       check_exit_code=False)

		del(self.device_details[port_name])

            except Exception as e:
                LOG.debug("port_removed failed for %(device)s: %(e)s",
                          {'device': device, 'e': e})
                resync = True

        return resync

    def daemon_loop(self):
        '''
        Runs a check periodically to determine if new ports were added or
        removed.  
        '''

        LOG.info(_LI("Ratekeeper Agent RPC Daemon Started!"))
        device_info = None
        sync = True
        succesive_exceptions = 0

        while self.run_daemon_loop:
            try:

                start = time.time()
                device_info = self.scan_devices(previous=device_info, sync=sync)

                if sync:
                    LOG.info(_LI("Agent out of sync with plugin!"))
                    sync = False

                if self._device_info_has_changes(device_info):
                    LOG.debug("Agent loop found changes! %s", device_info)
                    try:
                        sync = self.process_network_devices(device_info)
                    except Exception:
                        LOG.exception(_LE("Error in agent loop. Devices info: %s"),
                                  device_info)
                        sync = True

                # sleep till end of polling interval
                elapsed = (time.time() - start)
                if (elapsed < self.polling_interval):
                    time.sleep(self.polling_interval - elapsed)
                else:
                    LOG.debug("Loop iteration exceeded interval "
                              "(%(polling_interval)s vs. %(elapsed)s)!",
                              {'polling_interval': self.polling_interval,
                               'elapsed': elapsed})

                succesive_exceptions = 0

            except Exception as e:
                # The agent should retry a few times, in case something
                # bubbled up.  A successful provision loop will reset the
                # timer.
                succesive_exceptions += 1
                LOG.exception(e)
                if succesive_exceptions == 3:
                    LOG.error(_LE("RK: Multiple exceptions have been "
                                  "encountered.  The agent is unable to "
                                  "proceed.  Exiting."))
                    raise
                else:
                    LOG.warn(_LW("RK: Error has been encountered and logged.  The "
                             "agent will retry again."))


    def _handle_sigterm(self, signum, frame):
        LOG.debug("RK: Agent caught SIGTERM, quitting daemon loop.")
        self.run_daemon_loop = False
        if self.quitting_rpc_timeout:
            self.set_rpc_timeout(self.quitting_rpc_timeout)

    def set_rpc_timeout(self, timeout):
        for rpc_api in (self.plugin_rpc, self.state_rpc):
            rpc_api.client.timeout = timeout

class RkRpcCallbacks(object):

    def __init__(self, context, agent):
        super(RkRpcCallbacks, self).__init__()
        self.context = context
        self.agent = agent

    def port_update(self, context, **kwargs):
        '''
        Invoked to indicate that a port has been updated within Neutron.
        '''
        LOG.debug("RK: port_update RPC received for port: %s", kwargs)
	port_id = None
	if 'port' in kwargs:
	    # update sent by neutron server
            port_info = kwargs.get('port')
	    port_info['port_id'] = port_info['id']
	else:
	    # update sent by rk driver
	    port_info = kwargs.get('port_info')

	port_id = port_info.get('port_id')
	device_id = self._get_tap_device_name(port_id)
        self.agent.updated_devices.add(device_id)

    def _get_tap_device_name(self, interface_id):
        if not interface_id:
            LOG.warning(_LW("Invalid Interface ID, will lead to incorrect "
                            "tap device name"))
        tap_device_name = common_const.TAP_DEVICE_PREFIX + interface_id[0:11]
        return tap_device_name


def main():

    agent_common_config.register_agent_state_opts_helper(cfg.CONF)
    agent_common_config.register_root_helper(cfg.CONF)

    # Read in the command line args
    common_config.init(sys.argv[1:])
    common_config.setup_logging()

    polling_interval = cfg.CONF.RATEKEEPER_AGENT.polling_interval
    rk_intf = cfg.CONF.RATEKEEPER_AGENT.rk_intf

    # Build then run the agent
    try:
    	agent = HpRatekeeperNeutronAgent(polling_interval, rk_intf)
    except RuntimeError as e:
        LOG.error(_LE("RK: %s Agent terminated!"), e)
        sys.exit(1)
    signal.signal(signal.SIGTERM, agent._handle_sigterm)

    # Start everything.
    LOG.info(_LI("RK: Ratekeeper Agent initialized and running..."))
    agent.daemon_loop()
    sys.exit(0)


if __name__ == "__main__":
    main()
