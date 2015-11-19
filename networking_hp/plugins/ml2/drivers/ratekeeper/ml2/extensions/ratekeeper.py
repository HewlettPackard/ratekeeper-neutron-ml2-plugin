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

from neutron.api import extensions
from neutron.api.v2 import attributes as attr

from oslo_log import log
from neutron.i18n import _LE
LOG = log.getLogger(__name__)

RK_MIN_RATE = rk_const.RK_MIN_RATE
RK_MAX_RATE = rk_const.RK_MAX_RATE

# Attribute Map
EXTENDED_ATTRIBUTES_2_0 = {
    'networks': { 
            RK_MIN_RATE: {
		'allow_post': True, 
		'allow_put': True,
                'default': attr.ATTR_NOT_SPECIFIED,
		'convert_to': attr.convert_to_int,
		'validate': {'type:non_negative': None},
                'is_visible': True},
            RK_MAX_RATE: {
		'allow_post': True, 
		'allow_put': True,
                'default': attr.ATTR_NOT_SPECIFIED,
		'convert_to': attr.convert_to_int,
		'validate': {'type:non_negative': None},
                'is_visible': True},
    },
    'ports': {
            RK_MIN_RATE: {
		'allow_post': True, 
		'allow_put': True,
                'default': attr.ATTR_NOT_SPECIFIED,
		'convert_to': attr.convert_to_int,
		'validate': {'type:non_negative': None},
                'is_visible': True},
            RK_MAX_RATE: {
		'allow_post': True, 
		'allow_put': True,
                'default': attr.ATTR_NOT_SPECIFIED,
		'convert_to': attr.convert_to_int,
		'validate': {'type:non_negative': None},
                'is_visible': True},
    }
}

class Ratekeeper(extensions.ExtensionDescriptor):

    @classmethod
    def get_name(cls):
        return "Ratekeeper QoS Ratelimit Extension"

    @classmethod
    def get_alias(cls):
        return "ratekeeper"

    @classmethod
    def get_description(cls):
        return ("Ratekeeper extra options configuration for NETWORKS/PORTS. "
                "QoS min/max rates can be specified for each network/port")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/neutron/ratekeeper/api/v2.0"

    @classmethod
    def get_updated(cls):
        return "2015-04-16T12:00:00-00:00"

    def get_extended_resources(self, version):
        if version == "2.0":
            return EXTENDED_ATTRIBUTES_2_0
        else:
            return {}

