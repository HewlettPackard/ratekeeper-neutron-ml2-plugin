#!/bin/bash
#
# devstack/plugin.sh
# Functions to control the configuration and operation of the HP Ratekeeper
# bandwidth guarantee solution
# Dependencies:
#
# ``functions`` file
# ``DEST`` must be defined
# ``STACK_USER`` must be defined

# ``stack.sh`` calls the entry points in this order:
#

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set +o xtrace

# HP Networking-HP DIR.
HP_NETWORKING_DIR=$DEST/networking-hp

# Entry Points
# ------------

function copy_intree_nova_dependencies {
    echo "RK: Copying HP Ratekeeper's nova in-tree dependencies"
    cp $HP_NETWORKING_DIR/patches/nova/ratekeeper_monkey_patch.py $NOVA_DIR/nova/ratekeeper_monkey_patch.py
    cp $HP_NETWORKING_DIR/patches/nova/compute/resources/portspeed.py $NOVA_DIR/nova/compute/resources/portspeed.py
    cp $HP_NETWORKING_DIR/patches/nova/scheduler/filters/port_speed_filter.py $NOVA_DIR/nova/scheduler/filters/port_speed_filter.py
}

function copy_intree_neutron_dependencies {
    echo "RK: Copying HP Ratekeeper's neutron in-tree dependencies"
    cp $HP_NETWORKING_DIR/patches/neutron/cmd/eventlet/plugins/rk_neutron_agent.py $NEUTRON_DIR/neutron/cmd/eventlet/plugins/rk_neutron_agent.py
    mkdir -p $NEUTRON_DIR/neutron/plugins/ml2/drivers/hp/ratekeeper && cp $HP_NETWORKING_DIR/patches/neutron/plugins/ml2/drivers/hp/ratekeeper/mech_hp_ratekeeper.py $NEUTRON_DIR/neutron/plugins/ml2/drivers/hp/ratekeeper
    touch $NEUTRON_DIR/neutron/plugins/ml2/drivers/hp/__init__.py
    touch $NEUTRON_DIR/neutron/plugins/ml2/drivers/hp/ratekeeper/__init__.py
    ROOTWRAP_PATH=etc/neutron/rootwrap.d
    RK_ROOTWRAP_FILENAME=ratekeeper.filters
    RK_ROOTWRAP_FILE=$ROOTWRAP_PATH/$RK_ROOTWRAP_FILENAME
    cp $HP_NETWORKING_DIR/$RK_ROOTWRAP_FILE $NEUTRON_DIR/$ROOTWRAP_PATH
}

# Only for horizon version v2014.2.3
function copy_optional_intree_horizon_dependencies {
    echo "RK: Copying HP Ratekeeper's horizon in-tree dependencies"
    FILE='/openstack_dashboard/dashboards/admin/networks/ports/tables.py'
    cp $HP_NETWORKING_DIR/patches/horizon/$FILE $HORIZON_DIR/$FILE
    FILE='openstack_dashboard/dashboards/project/networks/ports/forms.py'
    cp $HP_NETWORKING_DIR/patches/horizon/$FILE $HORIZON_DIR/$FILE
    FILE='openstack_dashboard/dashboards/project/networks/ports/tables.py'
    cp $HP_NETWORKING_DIR/patches/horizon/$FILE $HORIZON_DIR/$FILE
    FILE='openstack_dashboard/dashboards/project/networks/ports/views.py'
    cp $HP_NETWORKING_DIR/patches/horizon/$FILE $HORIZON_DIR/$FILE
    FILE='openstack_dashboard/dashboards/project/networks/templates/networks/ports/_detail_overview.html'
    cp $HP_NETWORKING_DIR/patches/horizon/$FILE $HORIZON_DIR/$FILE
}

function start_ratekeeper_agent {
    RK_AGENT_BINARY="$NEUTRON_BIN_DIR/neutron-hp-ratekeeper-agent"
    echo "RK: Starting Ratekeeper Agent"
    echo "RK: python $RK_AGENT_BINARY --config-file $NEUTRON_CONF --config-file /$RK_CONF_FILE"
    run_process rk-agent "python $RK_AGENT_BINARY --config-file $NEUTRON_CONF --config-file /$RK_CONF_FILE"
}

function add_ratekeeper_config {
    RK_CONF_PATH=etc/neutron/plugins/ml2
    RK_CONF_FILENAME=ml2_conf_ratekeeper.ini
    RK_CONF_FILE=$RK_CONF_PATH/$RK_CONF_FILENAME
    echo "RK: Adding configuration file for HP Ratekeeper"
    cp $HP_NETWORKING_DIR/$RK_CONF_FILE /$RK_CONF_FILE
}

function configure_ratekeeper_config {
    echo "RK: Configuring ml2_conf_ratekeeper.ini for HP Ratekeeper"
    iniset /$RK_CONF_FILE ratekeeper default_min_rate $RK_MIN_RATE
    iniset /$RK_CONF_FILE ratekeeper default_max_rate $RK_MAX_RATE
    iniset /$RK_CONF_FILE ratekeeper_agent polling_interval $RK_POLLING_INTERVAL
}

function run_rk_alembic_migration {
    echo "RK: Creating HP Ratekeeper tables"
    $NEUTRON_BIN_DIR/neutron-hp-ratekeeper-db-manage --config-file $NEUTRON_CONF --config-file /$Q_PLUGIN_CONF_FILE upgrade head
}

function install_networking_ratekeeper {
    echo "RK: Installing HP Ratekeeper"
    setup_develop $HP_NETWORKING_DIR
}

# main loop
if is_service_enabled rk-ml2plugin; then
    if [[ "$1" == "source" ]]; then
        # no-op
        :   
    elif [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
        # no-op
        :   
    elif [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo "RK: stack install"
        copy_intree_neutron_dependencies
        copy_intree_nova_dependencies
        install_networking_ratekeeper
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo "RK: stack post-config"
        echo "RK: Q_PLUGIN_CONF_FILE: $Q_PLUGIN_CONF_FILE"
        run_rk_alembic_migration
    elif [[ "$1" == "stack" && "$2" == "post-extra" ]]; then
        # no-op 
        :   
    fi      

    if [[ "$1" == "unstack" ]]; then
        # no-op
        :   
    fi      

    if [[ "$1" == "clean" ]]; then
       # no-op
       :
    fi
fi

if is_service_enabled rk-agent; then
    if [[ "$1" == "source" ]]; then
        # no-op
        :   
    elif [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
        # no-op
        :   
    elif [[ "$1" == "stack" && "$2" == "install" ]]; then
        if ! is_service_enabled rk-ml2plugin; then
            echo "RK: stack install"
            copy_intree_neutron_dependencies
            copy_intree_nova_dependencies
            install_networking_ratekeeper
        fi
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo "RK: stack post-config"
        add_ratekeeper_config
        configure_ratekeeper_config
        start_ratekeeper_agent
    elif [[ "$1" == "stack" && "$2" == "post-extra" ]]; then
        # no-op 
        :   
    fi      

    if [[ "$1" == "unstack" ]]; then
        # no-op
        :   
    fi      

    if [[ "$1" == "clean" ]]; then
       # no-op
       :
    fi
fi

# Restore xtrace
$XTRACE

