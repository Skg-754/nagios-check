#!/usr/bin/env python3

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
from utils import processExec, parseSnmpSingleResult 
#from   import processExec 

# setting the parser

desc='''
	 
'''

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('-H','--host', 		dest='host', 			required=True, 		help='The host IP address')
parser.add_argument('-c','--community', 	dest='community', 		required=True, 		help='SNMP community')
parser.add_argument('-v','--verbose',		dest='verbose',			action='store_true',	help='Verbose mode')
args = parser.parse_args()

host 		= args.host
community 	= args.community
verbose 	= args.verbose

result={}

#
# Getting Description
#

oid = 'hrStorageDescr'
req = 'snmpwalk -v 2c -c {} {} {}'.format(community, host, oid)
if verbose : 
	print(req)
returnCode, returnMessage = processExec(req) 

if returnCode != 0 :
	print('error')
else :
	returnMessage = returnMessage.split('\n')[:-1]
	for line in returnMessage :  
		data = parseSnmpSingleResult(line)
		if verbose :
			print(data)
		index = data['index']
		value = data['value']
		result[index] = {}
		result[index]["descr"]=value

#
# Getting the allocation unit
#

oid = 'hrStorageAllocationUnits'
req = 'snmpwalk -v 2c -c {} {} {}'.format(community, host, oid)
if verbose : 
	print(req)
returnCode, returnMessage = processExec(req) 

if returnCode != 0 :
	print('error')
else :
	returnMessage = returnMessage.split('\n')[:-1]
	for line in returnMessage :  
		data = parseSnmpSingleResult(line)
		if verbose :
			print(data)	
		index = data['index']
		value = data['value']
		result[index]['allocationUnitValue']=value.split(' ')[0]
		result[index]['unit']=value.split(' ')[1]


#
# Getting Storage size
#

oid = 'hrStorageSize'
req = 'snmpwalk -v 2c -c {} {} {}'.format(community, host, oid)
if verbose : 
	print(req)
returnCode, returnMessage = processExec(req) 

if returnCode != 0 :
	print('error')
	print(returnMessage)
else :
	returnMessage = returnMessage.split('\n')[:-1]
	for line in returnMessage :  
		data = parseSnmpSingleResult(line)
		if verbose :
			print(data)	
		index = data['index']
		value = data['value']
		result[index]['size']=value

#
# Getting Storage size
#

oid = 'hrStorageUsed'
req = 'snmpwalk -v 2c -c {} {} {}'.format(community, host, oid)
if verbose : 
	print(req)
returnCode, returnMessage = processExec(req) 

if returnCode != 0 :
	print('error')
	print(returnMessage)
else :
	returnMessage = returnMessage.split('\n')[:-1]
	for line in returnMessage :  
		data = parseSnmpSingleResult(line)
		if verbose :
			print(data)	
		index = data['index']
		value = data['value']
		result[index]['used']=value


#
# Calculating the size and values in octet
#
for key, val in result.items() :
	result[key]['size'] = int(val['size'])*int(val['allocationUnitValue'])
	result[key]['used'] = int(result[key]['used'])*int(val['allocationUnitValue'])
	if result[key]['unit'] == 'Bytes' : 
		result[key]['size'] = result[key]['size']/1024/1024
		result[key]['unit'] = 'MB'
		result[key]['used'] = result[key]['used']/1024/1024

#
# Getting use percent
#
for key, val in result.items() :
	result[key]['percentUsed'] = result[key]['used']/result[key]['size']*100

#
# Reading the table
#
print('Result for host {}'.format(host))
print(''.ljust(7+60+18+18+10+10+18,'-'))
header = ' {} | {} | {} | {} | {} | {} '.format(
	'SNMP ID'.ljust(7),
	'Storage Description'.ljust(60),
	'Size'.ljust(18),
	'Used'.ljust(18),
	'Unit'.ljust(10),
	'% Used'.ljust(10)
	)
print(header)
print(''.ljust(7+60+18+18+10+10+18,'-'))

for key, val in result.items() :

	formatted = ' {} | {} | {} | {} | {} | {} '.format(
		key.ljust(7),
		val['descr'].ljust(60), 
		str(val['size']).ljust(18),
		str(val['used']).ljust(18),
		val['unit'].ljust(10),
		(str(round(val['percentUsed'],2))+' %').ljust(10)
                )
	print(formatted)





