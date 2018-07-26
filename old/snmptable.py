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


import subprocess 
import argparse

# setting the parser

desc='''
	'''

parser = argparse.ArgumentParser(description=desc)

parser.add_argument('-H',	'--host', 		dest='host', 			required=True, 				help='The host IP address')
parser.add_argument('-c',	'--community', 		dest='community', 		required=True, 				help='SNMP community')
parser.add_argument('-to',	'--tableOid',		dest='tableOid',		required=True,				help='oid of the table to check')
parser.add_argument('-io',	'--indexOid',		dest='indexOid',		required=True,				help='the column to take as index')
parser.add_argument('-co',	'--columnOid',		dest='columnOid',		default=[], nargs='*',			help='oids of the columns to get')
parser.add_argument('-ui',	'--updateIndex',	dest='updateIndex',		action='store_true',			help='refresh the id list')
parser.add_argument('-si',	'--selectedIndex',	dest='selectedIndex',		default=[], nargs='*', 			help='list of index to check')
parser.add_argument('-v', 	'--verbose', 		dest='verbose', 		action="store_true",		 	help='verbose mode')

args = parser.parse_args()

host 			= args.host
community 		= args.community
tableOid		= args.tableOid
numericalTableOid	= ''
indexOid 		= args.indexOid
columnOid		= args.columnOid
updateIndex 		= args.updateIndex
selectedIndex 		= args.selectedIndex
verbose 		= args.verbose

def processExec (request) :
	
	if verbose : 
		print(request)	
	process = subprocess.Popen(request, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()
	returnMessage = ''
	returnCode = process.returncode
	if returnCode == 0 : 
		returnMessage = stdout.decode('utf-8')
	else :
		returnMessage = dtderr.decode('utf-8')
	return returnCode, returnMessage

# change string oid to numerical oid
request = 'snmptranslate -On {}'.format(tableOid)
returnCode, returnMessage = processExec(request)
if returnCode != 0 : 
	print('error while getting table numerical oid')
else : 
	numericalTableOid = returnMessage
	if verbose : 
		print(numericalTableOid)

def parseSnmpSingleResult(message) :
	print(message)
	message = message.replace('\n','')
	result = {} 
	result['columnOid'] 	= message.split(' = ')[0].split('.')[0]
	result['index']		= message.split(' = ')[0].split('.')[1]
	result['valueType']	= message.split(' = ')[1].split(': ')[0]
	result['value']		= message.split(' = ')[1].split(': ')[1]
	return result


def getSnmpValue (host, community, oid) : 
	print('to be implemented') 

def getNextSnmpValue (host, community, oid) :

	request = 'snmpgetnext -v 2c -c {} -On {} {}'.format(community, host, oid)
	returnCode, returnMessage = processExec(request)	
	if returnCode != 0 :
		print('error')
		return False
	else : 
		return parseSnmpSingleResult(returnMessage)

def getSnmpTableColumn (host, community, columnOid) :
	print('to be implemented')		


def getSnmpTable (host, community, tableOid, indexOid, columnOid=False, selectedIndex=False) : 	
	
	index = 0
	columnNb = 0
	crtOid = tableOid
	result = {}
	def columnLoop (crtOid, index) :
		line = getNextSnmpValue(host, community, '{}.{}'.format(crtOid, index))
		print(line)
		if line['columnOid'] == crtOid or index == 0 :			
			
			crtOid = line['columnOid']
			if not line['index'] in result.keys() :
				result[line['index']] = {}
			result[line['index']][line['columnOid']] = line['value']
		
			index = line['index']
			columnLoop(crtOid, index)
		else :
			print('end of column')
	columnLoop(crtOid, index)
	return result	





result = getSnmpTable( host, community, tableOid, indexOid, columnOid, selectedIndex)
print(result)




