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

from oslo_config import cfg

ratekeeper_opts = [
    cfg.IntOpt('default_min_rate', default=10000,
               help="Default minimum bandwidth rate"),
    cfg.IntOpt('default_max_rate', default=10000,
                help="Default maximum bandwidth rate"),
]

# Ratekeeper Agent related config read from ml2_conf_ratekeeper.ini and neutron.conf

rk_agent_opts = [
    cfg.IntOpt('polling_interval', default=2,
               help="The number of seconds the agent will wait between polling for local device changes."),
    cfg.StrOpt('rk_intf', default="eth0",
                help="Data interface"),
]

def register_agent_opts():
    cfg.CONF.register_opts(ratekeeper_opts, "RATEKEEPER")
    cfg.CONF.register_opts(rk_agent_opts, "RATEKEEPER_AGENT")
