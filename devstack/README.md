## devstack-plugin for HP Ratekeeper Neutron plugin integration

This devstack external plugin installs the HP plugin library
so that the Neutron HP Ratekeeper ML2 mechanism driver 
can be enabled.

## Enabling in Devstack

1. Download DevStack

2. Add this repo as an external repository in local.conf::

    ```
    [[local|localrc]]
    enable_plugin networking-hp https://github.com/HewlettPackard/ratekeeper-neutron-ml2-plugin
    ```

3. Add the following required flags in local.conf to enable the HP Ratekeeper ML2 MechanismDriver::

    Q_ML2_PLUGIN_MECHANISM_DRIVERS=hp_ratekeeper
    Q_ML2_PLUGIN_EXT_DRIVERS=hp_ratekeeper_ext

    enable_service rk-ml2plugin

5. Add the following required flags in local.conf to enable the HP Ratekeeper agent on compute nodes::

    enable_service rk-agent

6. Optionally add the following lines to specify different default min/max rates (default is 10GB)::

    RK_MIN_RATE=4000 #4G
    RK_MAX_RATE=4000 #4G

    [[post-config|/etc/neutron/plugins/ml2/ml2_conf.ini]]
    [ratekeeper]
    default_min_rate=$RK_MIN_RATE
    default_max_rate=$RK_MAX_RATE

7. Read the settings file for more details.

8. run ``stack.sh``

## Example

Sample local.conf::

    [[local|localrc]]
    enable_plugin networking-hp https://github.com/HewlettPackard/ratekeeper-neutron-ml2-plugin

    disable_service n-net
    enable_service q-svc
    enable_service q-agt
    enable_service q-dhcp
    enable_service q-l3
    enable_service q-meta
    enable_service neutron
    enable_service n-novnc
    enable_service rk-ml2plugin
    enable_service rk-agent

    RK_MIN_RATE=4000 #4G
    RK_MAX_RATE=4000 #4G

    [[post-config|/etc/neutron/plugins/ml2/ml2_conf.ini]]
    [ratekeeper]
    default_min_rate=$RK_MIN_RATE
    default_max_rate=$RK_MAX_RATE


## References

http://docs.openstack.org/developer/devstack/plugins.html#externally-hosted-plugins
