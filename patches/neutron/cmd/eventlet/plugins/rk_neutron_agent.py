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

import sys

from networking_hp.plugins.ml2.drivers.ratekeeper.agent import (
    hp_ratekeeper_neutron_agent as rk_agent)
from networking_hp.plugins.ml2.drivers.ratekeeper.common import (
    config as rk_config)

from neutron.common import config as common_config


def main():
    rk_config.register_agent_opts()
    common_config.init(sys.argv[1:])
    common_config.setup_logging()
    rk_agent.main()

if __name__ == "__main__":
    main()
