#!/usr/bin/env python

import getopt
import os.path
import sys

# usage: parser.py -i <inputfile>


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hi:", "ifile=")
        if not opts:
            print 'No options supplied. For help use -h'
            sys.exit(2)
    except getopt.GetoptError:
        print 'parser.py -i <inputfile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'parser.py -i <inputfile>'
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
    uri = dict['OS_AUTH_URL'].replace(':5000/', '')
    with open('config.conf', 'w') as config_file:
        seq = ['[murano]\n',
               'horizon_url = ' + uri +'/dashboard/\n',
               'murano_url = ' + uri + ':8082\n',
               'user = ' + dict['OS_USERNAME'] + '\n',
               'password = ' + dict['OS_PASSWORD'] + '\n',
               'tenant = ' + dict['OS_TENANT_NAME'] + '\n',
               'keystone_url = ' + dict['OS_AUTH_URL'] + 'v3\n']
        config_file.writelines(seq)

if __name__ == "__main__":
    inputfile = main(sys.argv[1:])
    if not os.access(inputfile, os.R_OK):
        print "Cannot read the file: {0}. It may or not may exist".format(
            inputfile)
        sys.exit(2)
    dict = read_values(inputfile)
    create_config(dict)