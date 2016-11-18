#!/usr/bin/env python

from __future__ import print_function

import getopt
import os.path
import subprocess
import sys

# usage: parser.py -i <inputfile>


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hi:", "ifile=")
        if not opts:
            print('No options supplied. For help use -h')
            sys.exit(2)
    except getopt.GetoptError:
        print('parser.py -i <inputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('parser.py -i <inputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
            return inputfile


def read_values(inputfile):
    with open(inputfile, 'r') as inputfile:
        dict = {k: v for line in inputfile if '=' in line for (k, v) in (
            line.replace('\'', '').strip('export ').strip().split('=', 1),)}
    return dict


def create_config(dict):
    cmd = subprocess.check_output(
        'openstack endpoint list --long -c PublicURL -f \'value\'', shell=True)
    keystone_url = None
    for row in cmd.split('\n'):
        if '5000' in row:
                keystone_url = row.replace('v2.0', '')
    uri = keystone_url.replace(':5000/', '')
    with open('config.conf', 'w') as config_file:
        seq = ['[murano]\n',
               'horizon_url = ' + uri + '/horizon/\n',
               'murano_url = ' + uri + ':8082\n',
               'user = ' + dict['OS_USERNAME'] + '\n',
               'password = ' + dict['OS_PASSWORD'] + '\n',
               'tenant = ' + dict['OS_TENANT_NAME'] + '\n',
               'keystone_url = ' + keystone_url + 'v3\n']
        config_file.writelines(seq)

if __name__ == "__main__":
    inputfile = main(sys.argv[1:])
    if not os.access(inputfile, os.R_OK):
        print("Cannot read the file: {0}. It may or not may exist".format(
            inputfile))
        sys.exit(2)
    dict = read_values(inputfile)
    create_config(dict)
