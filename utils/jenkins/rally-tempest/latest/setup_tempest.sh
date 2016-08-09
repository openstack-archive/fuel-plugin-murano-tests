#!/bin/bash -xe

source /home/rally/openrc

rally-manage db recreate
rally deployment create --fromenv --name=tempest
rally verify install --source /var/lib/tempest
rally verify genconfig
rally verify showconfig
rally verify installplugin --source https://github.com/openstack/murano
rally verify listplugins
