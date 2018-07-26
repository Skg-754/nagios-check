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
import datetime
import sys
import json
import os
import re

# setting the parser

desc='''
	 
'''

parser = argparse.ArgumentParser(description=desc)

parser.add_argument('-H','--host', 		dest='host', 			required=True, 		help='The host IP address')
parser.add_argument('-c','--community', 	dest='community',		required=True,		help='SNMP community')
parser.add_argument('-n','--switchNumber', 	dest='switchNumber',		default=-1, type=int,	help='Switch Number (dot not use with -ir)')
parser.add_argument('-ir','--interfaceFilter', 	dest='interfaceFilter',		default='',		help='Interface Name (regex) (do not use with -n)')
parser.add_argument('-F', '--fullScan', 	dest='fullScan', 		action='store_true', 	help='Rescan all the snmp interfaces ids')
parser.add_argument('-l', '--listAll', 		dest='listAll', 		action='store_true', 	help='List all the stored interfaces ids')
parser.add_argument('-f', '--snmpIdFile',	dest='snmpIdFile', 		default='snmpId.json', 	help='File containing the snmp interfaces ids (create new file if not found)')
parser.add_argument('-v', '--verbose', 		dest='verbose', 		action='store_true', 	help='Verbose mode')
parser.add_argument('-vv', '--superVerbose', 	dest='superVerbose', 		action='store_true', 	help='Super Verbose mode')
args = parser.parse_args()

host = args.host
community = args.community


if args.switchNumber > 0 :
	interfaceFilter = re.compile("^.*-{}\/\d*\/\d*$".format(args.switchNumber))
else :
	interfaceFilter = re.compile(args.interfaceFilter)


fullScan = args.fullScan
listAll = args.listAll
snmpIdFile = args.snmpIdFile
verbose = args.verbose
superVerbose = args.superVerbose
snmpId = {}
snmpValues = {}


def subprocessExec (req) : 
	'''
		Exec a subprocess and return a tuple containing the return code and the return message of the command.
	'''
	if superVerbose : 
		print(req)
	process = subprocess.Popen(req, shell=True, stdout=subprocess.PIPE)	
	stdout, stderr = process.communicate()	
	returnMessage = ''
	returnCode = process.returncode
	if process.returncode == 0 :
		returnMessage = stdout
	else : 
		returnMessage = stderr
		print('error : {}'.format(stderr.decode('utf-8')))
	return returnCode, returnMessage.decode('utf-8')



def snmpgetReturnParser (message, oid=None) : 
	'''
		Parse the output of a snmpget command and return the value
	'''
	
	value = message.split(' = ')[1].split(': ')[1].replace('\n','')
	if oid : 
		valueId = message.split(' = ')[0].replace(oid, '')[1:]
		return valueId, value
	else :
		return value
	# valueType = line.split(' = ')[1].split(': ')[0]
	
	

def snmpIdFilter (regex) :
	'''
		Return an array containing the snmp id of the interfaces matching the regex given
	'''
	matchingIds = []
	for interfaceDescr, snmpId  in snmpIds.items() : 
		if re.match(regex, interfaceDescr) :		
			matchingIds.append(snmpId)
	return matchingIds

def getSnmpId () :
	'''
		Scan all the available interfaces
		Collect the SNMP if of the interfaces and store them in the file given (or in a default file)
	'''
	if verbose :
		print('starting snmp interfaces ID scan...')
	
	oid = 'IF-MIB::ifDescr'
	request = 'snmpwalk -v 2c -c {} {} {}'.format(community, host, oid)		

	returnCode, returnMessage = subprocessExec(request)

	if returnCode == 0 : 
		lines = returnMessage.split('\n')[:-1]
		snmpIds = {}

		for line in lines :
			valueId, value = snmpgetReturnParser(line, oid)
			snmpIds[value] = valueId

		# writting the file
		if verbose : 
			print('id collected. Writting file...')
 
		with open(snmpIdFile, 'w') as file :
			file.write(json.dumps(snmpIds))
			if verbose : 
				print('file written')



# check if a id file exists
if os.path.isfile(snmpIdFile) and not fullScan : 
	with open(snmpIdFile) as file :
		snmpIds = json.loads(file.read()) 
else : 
	if verbose :
		print('snmp idFile not found')
	getSnmpId()



if listAll : 
	for key, val in snmpIds.items() :

		formatted = '{} | {} '.format(
			val.ljust(5),
			key.ljust(20))
		print(formatted)

filteredList = snmpIdFilter(interfaceFilter)


def getSnmpValues(oid, idList, label) :

	for snmpId in idList : 
		
		if not snmpId in snmpValues.keys() : 
			snmpValues[snmpId] = {}
		req = 'snmpget -v 2c -c {} {} {}.{}'.format(community, host, oid, snmpId)
		returnCode, returnMessage = subprocessExec(req)

		if returnCode == 0 : 
			value = snmpgetReturnParser(returnMessage)
			snmpValues[snmpId][label] = value


# collecting the informations

	
oid = 'IF-MIB::ifDescr'
getSnmpValues(oid, filteredList, 'ifDescr')
if verbose : 
	print('ifDescr collected')
	
oid = 'IF-MIB::ifAlias'
getSnmpValues(oid, filteredList, 'ifAlias')
if verbose : 
	print('ifAlias collected')

oid = 'IF-MIB::ifOperStatus'
getSnmpValues(oid, filteredList, 'ifOperStatus')
if verbose : 
	print('ifOperStatus collected')

oid = 'IF-MIB::ifPhysAddress'
getSnmpValues(oid, filteredList, 'ifPhysAddress')
if verbose : 
	print('ifPhysAddress collected')

# oid = 'IF-MIB::ipAdEntIfIndex'
# getSnmpValues(oid, filteredList, 'ipAdEntIfIndex')
# if verbose : 
# 	print('ipAdEntIfIndex collected')



for val in snmpValues.values() :

	formatted = '{} | {} | {} | {} '.format(
		val['ifDescr'].ljust(15),
		val['ifAlias'].ljust(60), 
		val['ifOperStatus'].ljust(18),
		val['ifPhysAddress'].ljust(18)
                )
	print(formatted)



