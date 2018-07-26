#!/usr/bin/env python3

#####################################
#
#   File :         
#   Description :   
#   Langage :       Python3
#   Date :          
#   Author :        Skg-754
#   
#####################################


import sys
import os
import time

sys.path.insert(0, '../utils')

from utils import processExec, parseSnmpSingleResult

import argparse
import json

# setting the parser

desc='''
	'''

parser = argparse.ArgumentParser(description=desc)

parser.add_argument('-H',	'--host', 		    dest='host', 			required=True, 				help='The host IP address')
parser.add_argument('-u',	'--user', 		    dest='user', 		    required=True, 				help='The SSH user')
parser.add_argument('-p',	'--password',	    dest='password',	    required=True, 				help='The SSH password')
parser.add_argument('-f',	'--file-path',	    dest='path',	        required=True, 				help='The path to the status.dat file')
parser.add_argument('-v', 	'--verbose', 		dest='verbose', 		action="store_true",		help='verbose mode')

args = parser.parse_args()

host        = args.host
user        = args.user
password    = args.password
path        = args.path
verbose     = args.verbose

status      = None
statusFile  = 'status.dat'
hosts       = {}
services    = {}
maxFileAge  = 20

#
# Getting de status.dat file
#
request = 'sshpass -p {} scp {}@{}:{} ./'.format(password, user, host, path)
if verbose : 
    print(request)
returnCode, returnMessage = processExec(request)
if returnCode != 0 :
    print('error')
    print(returnMessage)
else : 
    if verbose :
        print('status.dat downloaded')

#
# Parsing the file
#
if os.path.isfile(statusFile) : 
    with open (statusFile) as file :
        status = file.read()
        # print(status)

        # separating each service or component
        status = status.split('\n\n')
        for element in status : 
            split = element.split(' {\n\t')
            # print(split)
            if len(split) > 1 :
                componentType = split[0]
                componentData = split[1]
                # print(componentType)
                # print('')
                componentData = componentData.replace('\n\t}','').split('\n\t')
                # print(componentData)
                # print('')
                
                infos = {}
                for info in componentData : 
                    key = info.split('=')[0]
                    val = info.split('=')[1]
                    infos[key] = val
                if componentType == 'info' :
                    print('checking date of the file')
                    crtTime = time.time()
                    delta = crtTime - int(infos['created'])
                    if delta > maxFileAge :
                        print('file to old : {} s'.format(delta))
                    else : 
                        print('file age ok : {} s'.format(delta))
                elif componentType == 'hoststatus' :
                    hosts[infos['host_name']] = infos
                elif componentType == 'servicestatus' :
                    if not infos['host_name'] in services.keys() : 
                        services[infos['host_name']] = {}
                    services[infos['host_name']][infos['service_description']] = infos

    #
    # listing the hosts
    # 
    if verbose : 
        for hostName, hostInfo in hosts.items() :
            print(hostName)
            #
            # listing services
            #
            if hostName in services.keys() :
                for serviceName, serviceInfo in services[hostName].items() : 
                    print('\t'+serviceName)
