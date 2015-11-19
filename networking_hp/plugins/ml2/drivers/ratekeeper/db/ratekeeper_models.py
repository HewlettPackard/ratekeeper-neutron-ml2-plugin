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

import sqlalchemy as sa
from sqlalchemy import orm

from neutron.db import model_base
from neutron.db import models_v2
from neutron.plugins.common import constants

from oslo_log import log

LOG = log.getLogger(__name__)

class VifProfile(model_base.BASEV2, model_base.NeutronBaseV2):

    """Schema profiling VIF attributes"""
    __tablename__ = 'hp_ml2_ratekeeper_vif_profile'

    vif_id = sa.Column(sa.String(255), primary_key=True)
    segment_id = sa.Column(sa.Integer)
    min_rate = sa.Column(sa.Integer)
    max_rate = sa.Column(sa.Integer)

    def __init__(self, vif_id=None, segment_id=None, min_rate=None, max_rate=None):
        LOG.debug("RK: __init__()") 
        self.vif_id = vif_id
        self.segment_id = segment_id
        self.min_rate = min_rate
        self.max_rate = max_rate

    def __repr__(self):
        return "<hp_ml2_ratekeeper_vif_profile (%s, %s, %s, %s)>" %\
            (repr(self.vif_id), repr(self.segment_id),
             repr(self.min_rate),
             repr(self.max_rate))


class VnetProfile(model_base.BASEV2, model_base.NeutronBaseV2):

    """Schema profiling VNET attributes"""
    __tablename__ = 'hp_ml2_ratekeeper_vnet_profile'

    vnet_id = sa.Column(sa.String(255), primary_key=True)
    min_rate = sa.Column(sa.Integer)
    max_rate = sa.Column(sa.Integer)

    def __init__(self, vnet_id=None, min_rate=None, max_rate=None):
        LOG.debug("RK: __init__()") 
        self.vnet_id = vnet_id
        self.min_rate = min_rate
        self.max_rate = max_rate

    def __repr__(self):
        return "<hp_ml2_ratekeeper_vnet_profile (%s, %s, %s)>" %\
            (repr(self.vnet_id),
             repr(self.min_rate),
             repr(self.max_rate))


