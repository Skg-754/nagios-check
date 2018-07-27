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
parser.add_argument('-mg',	'--general-mode',	dest='generalMode',	    action="store_true", 		help='General mode : print a global status of the remote nagios')
parser.add_argument('-mh',	'--host-mode',	    dest='hostMode',	    default="", 		        help='Host mode : print a specific host status of the remote nagios')
parser.add_argument('-ms',	'--service-mode',	dest='serviceMode',	    default="", 		        help='Service mode : print a specific service status of the remote nagios')
parser.add_argument('-v', 	'--verbose', 		dest='verbose', 		action="store_true",		help='verbose mode')

args = parser.parse_args()

# gettings the user args
host        = args.host
user        = args.user
password    = args.password
path        = args.path

verbose     = args.verbose

# script globals
status      = None
statusFile  = '_status.dat'
hosts       = {}
services    = {}
maxFileAge  = 20

# nagios output ini
nagiosStatusCode = {
	"OK" 		: 0,
	"WARNING" 	: 1,
	"CRITICAL" 	: 2,
	"UNKNOWN" 	: 3
}
statusCode=None
statusInformation=''
perfData=''

def nagiosOutput (statusCode, statusInformation, perfData='') : 
    '''
    Print the nagios output and end the script
    '''
    statusInformation = statusInformation.strip()   
    print('{} | {}'.format(statusInformation, perfData))
    sys.exit(statusCode)

def getFile () :
    '''
    Getting de status.dat file
    '''
    request = 'sshpass -p {} scp {}@{}:{} ./{}'.format(password, user, host, path, statusFile)
    if verbose : 
        print(request)
    returnCode, returnMessage = processExec(request)
    if returnCode != 0 :
        statusCode = nagiosStatusCode['UNKNOWN']
        statusInformation = ' UNABLE TO GET .dat FILE : {}'.format(returnMessage)
        nagiosOutput(statusCode, statusInformation)
    else : 
        if verbose :
            print('status.dat downloaded')

def parseFile() :
    '''
    Parsing the file
    '''
    if os.path.isfile(statusFile) : 
        with open (statusFile) as file :
            status = file.read()
            # separating each service or component
            status = status.split('\n\n')
            for element in status : 
                split = element.split(' {\n\t')
                if len(split) > 1 :
                    componentType = split[0]
                    componentData = split[1]
                    componentData = componentData.replace('\n\t}','').split('\n\t')

                    # storing the parsed information in temp dict
                    infos = {}
                    for info in componentData : 
                        key = info.split('=')[0]
                        val = info.split('=')[1]
                        infos[key] = val

                    # checking the file time
                    if componentType == 'info' :
                        if verbose : 
                            print('checking date of the file')
                        crtTime = time.time()
                        delta = crtTime - int(infos['created'])
                        if delta > maxFileAge :
                            statusCode = nagiosStatusCode['UNKNOWN']
                            statusInformation = 'ERROR : Remote nagios .dat file is {}s old (more than {}s) '.format(delta, maxFileAge)
                            nagiosOutput(statusCode, statusInformation)
                        else : 
                            if verbose : 
                                print('Remote nagios .dat file age checked : {} s'.format(delta))

                    # saving host status        
                    elif componentType == 'hoststatus' :
                        hosts[infos['host_name']] = infos

                    # saving service status
                    elif componentType == 'servicestatus' :
                        if not infos['host_name'] in services.keys() : 
                            services[infos['host_name']] = {}
                        services[infos['host_name']][infos['service_description']] = infos
                        
    else :
        statusCode = nagiosStatusCode['UNKNOWN']
        statusInformation = "ERROR : downloaded file seems not te be accessible"
        nagiosOutput(statusCode, statusInformation)

def printStatus() :
    '''
    listing the collected datas
    '''
    if verbose : 
        for hostName, hostInfo in hosts.items() :
            print(hostName)
            #
            # listing services
            #
            if hostName in services.keys() :
                for serviceName, serviceInfo in services[hostName].items() : 
                    print('\t'+serviceName)

def generalStatus () :
    '''
    Getting the general status of the remote nagios
    '''

    hostsNb = 0
    servicesNb = 0
    critical = 0
    criticalHosts = []
    warning = 0
    warningHosts = []
    unknown = 0
    unknownHosts = []    
    ok = 0

    # host status :                         current_state   plugin_output   performance_data    last_update
    # service status : service_description  current_state   plugin_output   performance_data    last_update
    
    for key, hostData in hosts.items() :       
        hostsNb += 1
        hostName = hostData['host_name']
        state = int(hostData['current_state'])

        if state == nagiosStatusCode['WARNING'] :
            if not hostName in warningHosts :
                warningHosts.append(hostName)
            warning +=1
        elif state == nagiosStatusCode['CRITICAL'] :
            if not hostName in criticalHosts :
                criticalHosts.append(hostName)
            critical += 1
        elif state == nagiosStatusCode['UNKNOWN'] :
            if not hostName in unknownHosts :
                unknownHosts.append(hostName)
            unknown +=1
        elif state == nagiosStatusCode['OK'] :
            ok +=1

        if hostName in services.keys() :
            for serviceName, serviceData in services[hostName].items() :
                servicesNb += 1    
                state = int(serviceData['current_state'])

                if state == nagiosStatusCode['WARNING'] :
                    if not hostName in warningHosts :
                        warningHosts.append(hostName)
                    warning +=1
                elif state == nagiosStatusCode['CRITICAL'] :
                    if not hostName in criticalHosts :
                        criticalHosts.append(hostName)
                    critical += 1
                elif state == nagiosStatusCode['UNKNOWN'] :
                    if not hostName in unknownHosts :
                        unknownHosts.append(hostName)
                    unknown +=1
                elif state == nagiosStatusCode['OK'] :
                    ok +=1


    statusInformation = ''
    statusCode = None
    if critical > 0 :
        statusInformation += 'CRITICAL : '
        statusCode = nagiosStatusCode['CRITICAL']
    elif warning > 0 :
        statusInformation += 'WARNING : '
        statusCode = nagiosStatusCode['WARNING']
    elif unknown > 0 : 
        statusInformation += 'UNKOWN : '
        statusCode = nagiosStatusCode['UNKOWN']
    elif ok == hostsNb + servicesNb :
        statusInformation += 'OK : '
        statusCode = nagiosStatusCode['OK']
    else :
        statusInformation += 'UNKOWN : '
        statusCode = nagiosStatusCode['UNKOWN']

    criticalHosts = str(criticalHosts).replace("["," ").replace("]"," ").replace("'","")
    warningHosts = str(warningHosts).replace("["," ").replace("]"," ").replace("'","")
    unknownHosts = str(unknownHosts).replace("["," ").replace("]"," ").replace("'","")

    statusInformation += 'TOTAL HOSTS :{}, TOTAL SERVICES :{}, CRITICAL :{} ({}), WARNING :{} ({}), UNKNOWN :{} ({}), OK : {}'.format(
        hostsNb, servicesNb, critical, criticalHosts, warning, warningHosts, unknown, unknownHosts, ok)  
    
    nagiosOutput(statusCode, statusInformation)

def hostStatus (hostName) :
    '''
    Getting the status of an host of the remote nagios
    '''
    #
    # Need to refactor
    #

    servicesNb = 0
    critical = 0
    criticalServices = []
    warning = 0
    warningServices = []
    unknown = 0
    unknownServices = [] 
    ok = 0
    okServices = [] 

    if hostName in hosts.keys() : 

        # host verfication
        hostData = hosts[hostName]
        state = int(hostData['current_state'])

        if state == nagiosStatusCode['WARNING'] :
            warning +=1
        elif state == nagiosStatusCode['CRITICAL'] :
            critical += 1
        elif state == nagiosStatusCode['UNKNOWN'] :
            unknown +=1
        elif state == nagiosStatusCode['OK'] :
            ok +=1
        
        # service verification
        if hostName in services.keys() :
            for serviceName, serviceData in services[hostName].items() :
                servicesNb += 1    
                state = int(serviceData['current_state'])

                if state == nagiosStatusCode['WARNING'] :
                    if not hostName in warningServices :
                        warningServices.append(serviceName)
                    warning +=1
                elif state == nagiosStatusCode['CRITICAL'] :
                    if not hostName in criticalServices :
                        criticalServices.append(serviceName)
                    critical += 1
                elif state == nagiosStatusCode['UNKNOWN'] :
                    if not hostName in unknownServices :
                        unknownServices.append(serviceName)
                    unknown +=1
                elif state == nagiosStatusCode['OK'] :
                    if not hostName in okServices :
                        okServices.append(serviceName)
                    ok +=1

        statusInformation = ''
        statusCode = None
        if critical > 0 :
            statusInformation += 'CRITICAL : '
            statusCode = nagiosStatusCode['CRITICAL']
        elif warning > 0 :
            statusInformation += 'WARNING : '
            statusCode = nagiosStatusCode['WARNING']
        elif unknown > 0 : 
            statusInformation += 'UNKOWN : '
            statusCode = nagiosStatusCode['UNKOWN']
        elif ok == servicesNb +1 :
            statusInformation += 'OK : '
            statusCode = nagiosStatusCode['OK']
        else :
            statusInformation += 'UNKOWN : '
            statusCode = nagiosStatusCode['UNKOWN']

        criticalServices = str(criticalServices).replace("["," ").replace("]"," ").replace("'","")
        warningServices = str(warningServices).replace("["," ").replace("]"," ").replace("'","")
        unknownServices = str(unknownServices).replace("["," ").replace("]"," ").replace("'","")

        statusInformation += 'HOST :{}, SERVICES :{}, CRITICAL :{} ({}), WARNING :{} ({}), UNKNOWN :{} ({}), OK : {}'.format(
            hostName, servicesNb, critical, criticalServices, warning, warningServices, unknown, unknownServices, ok)  
        
        nagiosOutput(statusCode, statusInformation)
        
    else :
        statusCode = nagiosStatusCode['UNKNOWN']
        statusInformation = 'ERROR : hostname "{}" not found on remote nagios'.format(hostName)

        nagiosOutput(statusCode, statusInformation)


#
# Script entry
#
if __name__ == "__main__":

    getFile()
    parseFile()
    if verbose :
        printStatus()
    if args.generalMode :
        if verbose : 
            print('### General Mode ###')
        generalStatus()
    elif args.hostMode != '' :
        if verbose : 
            print('### Host Mode : {} ###'.format(args.hostMode))   
        hostStatus(args.hostMode)
    elif args.serviceMode != '' :
        if verbose : 
            print('### Service Mode : {} ###'.format(args.serviceMode))   
        statusCode = nagiosStatusCode['UNKNOWN']
        statusInformation = 'ERROR : service mode is not implemented yet'
        nagiosOutput(statusCode, statusInformation)       
    else :
        statusCode = nagiosStatusCode['UNKNOWN']
        statusInformation = 'ERROR : please select a mode : -mg (general) -mh (host) -ms (service)'
        nagiosOutput(statusCode, statusInformation)