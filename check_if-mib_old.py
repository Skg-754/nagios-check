#!/bin/python3

#####################################
#
#   File :          check_if-mib.py
#   Description :   
#   Langage :       Python3
#   Date :          
#   Author :        Skg-754
#   
#####################################


import subprocess 
import argparse
import datetime
import sys
import json

# setting the parser

desc='''
	 
'''

parser = argparse.ArgumentParser(description=desc)

parser.add_argument('-H','--host', 	dest='host', 		required=True, 		help='The host IP address')
parser.add_argument('-C','--community', dest='community',	required=True,		help='SNMP community')
parser.add_argument('-v', '--verbose', 	dest='verbose', 	action='store_true', 	help='Verbose mode')

args = parser.parse_args()

host = args.host
community = args.community
verbose = args.verbose

result = {}

def snmpWalkParser (oid, valueName, resultArray) :
	request = 'snmpwalk -v 2c -c {} -CE {}.100 {} {} '.format(community, oid, host, oid)
	# request = 'snmpwalk -v 2c -c {} {} {} '.format(community, host, oid)
	if verbose : 
        	print(request) 
	
	result = subprocess.Popen(request, shell=True, stdout=subprocess.PIPE).stdout.read()
	result = result.decode('utf-8')
	
	lines = result.split('\n')[:-1]

	for line in lines :
		current = {}
		valueId = line.split(' = ')[0].replace(oid, '')[1:]
		valueType = line.split(' = ')[1].split(': ')[0]
		value = line.split(' = ')[1].split(': ')[1]
		if not valueId in resultArray.keys() :
			resultArray[valueId] = {}
		resultArray[valueId][valueName] = value	
		
	return resultArray

# requesting ifDescr
oid = 'IF-MIB::ifDescr'
result = snmpWalkParser(oid, 'ifDescr', result)

with open('interfacesId.txt', 'w') as file :
	file.write(json.dumps(result))

test = open('interfacesId.txt', 'r')
test = json.loads(test.read())


# requesting labels
#oid = 'IF-MIB::ifAlias'
#result = snmpWalkParser(oid, 'ifAlias', result)

# requesting status
#oid = 'IF-MIB::ifOperStatus'
#result = snmpWalkParser(oid, 'ifOperStatus', result)

# requesting mac addr
#oid = 'IF-MIB::ipNetToMediaPhysAddress'
#result = snmpWalkParser(oid, 'physAlias', result)

print('coucou')

# for val in test.values()  : 
# 	formatted = '{} |  | '.format(
# 		val['ifDescr'].ljust(10) 
# 		#val['ifAlias'].ljust(40), 
# 		#val['ifOperStatus'].ljust(20)
# 		) 
# 	print(formatted)






