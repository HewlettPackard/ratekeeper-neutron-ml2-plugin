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

from oslo_log import log 

import sqlalchemy.orm.exc as sa_exc

from neutron import context as ncontext
import neutron.db.api as db_api
from neutron.i18n import _LE 
from networking_hp.plugins.ml2.drivers.ratekeeper.db import (
    ratekeeper_models as rk_models)
from networking_hp.plugins.ml2.drivers.ratekeeper.common import (
    constants as rk_constants)


LOG = log.getLogger(__name__)


def create_vif_record(port_id, segment_id, min_rate, max_rate, db_session=None):
    """ 
    Create a vif_profile record.

    :param db_session: database session
    :param port_id: UUID representing the port
    :param network_id: UUID representing the network
    :param min_rate: minimun port rate in bytes
    :param max_rate: maximum port rate in bytes
    :returns: vif profile of given port
    """

    db_session = db_session or db_api.get_session()
    vif_profile = rk_models.VifProfile(vif_id=port_id,
					       segment_id=segment_id,
					       min_rate=min_rate,
					       max_rate=max_rate)
    db_session.add(vif_profile)
    db_session.flush()
    return vif_profile

def get_vif_profile(port_id, db_session=None):
    """
    Retrieve VifProfile of port

    :param port_id: UUID representing the network port
    :param db_session: database session
    :returns vif_profile of port
    """
    db_session = db_session or db_api.get_session()
    try:
        return (db_session.query(rk_models.VifProfile).
            filter_by(vif_id=port_id).one())
    except sa_exc.NoResultFound:
        return None


def delete_vif_record(vif_id, db_session=None):
    """
    Delete a vif_profile record

    :param vif_id: ID of remove interface
    :param db_session: database session
    """
    db_session = db_session or db_api.get_session()
    try:
        vif_profile = (db_session.query(rk_models.VifProfile).\
                   filter_by(vif_id=vif_id).one())
     	db_session.delete(vif_profile)
	db_session.flush()
    except:
        # no record was found, do nothing
        pass


def update_vif_segment_id(port_id, 
			  segment_id,
			  db_session=None):
    """
    Update rate limit of a vif

    :param db_session: database session
    :param port_id: UUID of port interface
    :param segment_id: id of network segment
    :returns: vif profile of given port
    """
    db_session = db_session or db_api.get_session()
    try:
    	vif_profile = (db_session.query(rk_models.VifProfile).
                   filter_by(vif_id=port_id).one())
        vif_profile.segment_id = segment_id
        db_session.flush()
    	return vif_profile
    except sa_exc.NoResultFound:
        return None

def update_vif_rate_limit(port_id, 
	 		  min_rate,
                          max_rate,
			  db_session=None):
    """
    Update rate limit of a vif

    :param db_session: database session
    :param port_id: UUID of port interface
    :param min_rate: minimun port rate in bytes
    :param max_rate: maximum port rate in bytes
    :returns: vif profile of given port
    """
    db_session = db_session or db_api.get_session()
    try:
    	vif_profile = (db_session.query(rk_models.VifProfile).
                   filter_by(vif_id=port_id).one())
        vif_profile.min_rate = min_rate
        vif_profile.max_rate = max_rate
        db_session.flush()
    	return vif_profile
    except sa_exc.NoResultFound:
        return None


def create_vnet_record(network_id, min_rate, max_rate, db_session=None):
    """ 
    Create a vnet_profile record.

    :param db_session: database session
    :param network_id: UUID representing the network
    :param min_rate: minimun port rate in bytes
    :param max_rate: maximum port rate in bytes
    :returns: vif profile of given port
    """
    db_session = db_session or d_api.get_session()
    vnet_profile = rk_models.VnetProfile(vnet_id=network_id,
					       min_rate=min_rate,
					       max_rate=max_rate)
    db_session.add(vnet_profile)
    db_session.flush()
    return vnet_profile

def get_vnet_profile(network_id, db_session=None):
    """
    Retrieve VnetProfile of network

    :param network_id: UUID representing the network
    :param db_session: database session
    :returns vnet_profile of network
    """
    db_session = db_session or db_api.get_session()
    try:
        return (db_session.query(rk_models.VnetProfile).
            filter_by(vnet_id=network_id).one())
    except sa_exc.NoResultFound:
        return None

def update_vnet_rate_limit(network_id, 
	 		  min_rate,
                          max_rate,
			  db_session=None):
    """
    Update rate limit of a vnet

    :param db_session: database session
    :param network_id: UUID of port interface
    :param min_rate: minimun port rate in bytes
    :param max_rate: maximum port rate in bytes
    :returns: vnet profile of given network
    """
    db_session = db_api.get_session()
    try: 
    	vnet_profile = (db_session.query(rk_models.VnetProfile).
                   filter_by(vnet_id=network_id).one())
        vnet_profile.min_rate = min_rate
        vnet_profile.max_rate = max_rate
        db_session.flush()
    	return vnet_profile
    except sa_exc.NoResultFound:
        return None


def delete_vnet_record(network_id, db_session=None):
    """
    Delete a vnet_profile record

    :param network_id: ID of remove interface
    :param db_session: database session
    """
    db_session = db_session or db_api.get_session()
    try:
        vnet_profile = (db_session.query(rk_models.VnetProfile).\
                   filter_by(vnet_id=network_id).one())
     	db_session.delete(vnet_profile)
	db_session.flush()
    except:
        # no record was found, do nothing
        pass
