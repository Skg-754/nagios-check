#!/bin/python3

#####################################
#
#   File :          getSnmpTable.py
#   Description :   Utility to display SNMP table into terminal
#   Langage :       Python3
#   Date :          
#   Author :        Skg-754
#   Depedencies :   SnmpTable.py
#
#####################################

from SnmpTable import *

import argparse

desc = '''
'''



parser = argparse.ArgumentParser(description=desc)

# GENERAL INFORMATIONS
parser.add_argument('-H',	'--host', 		dest='host', 			required=True, 			help='The host IP address')
parser.add_argument('-c',	'--community', 		dest='community', 		required=True, 			help='SNMP community')
parser.add_argument('-m',	'--mib-file',		dest='mibFile',			required=True,			help='Mib file of the table')
parser.add_argument('-to',	'--tableOid',		dest='tableOid',		required=True,			help='Table OID String') 	
parser.add_argument('-v',	'--verbose',		dest='verbose',			action='store_true',		help='Verbose mode')

# COLLECT OPTIONS
parser.add_argument('-cc', 	'--collect-columns',	dest='columns',			default=[], nargs='*',		help='Columns to be collected, by default all')

# PRINT OPTIONS
parser.add_argument('-pc',	'--print-columns',	dest='printColumns',		action='store_true',		help='Print the columns list')
parser.add_argument('-pi', 	'--print-indexes',	dest='printIndexes',		action='store_true',		help='Print the snmp indexes list')

# OUTPUT OPTIONS
parser.add_argument('-op',	'--output-print',	dest='outputPrint',		action='store_true',		help='print the collected datas in the terminal')
parser.add_argument('-oc',	'--output-csv',		dest='outputCsv',		default=False,			help='store the collected datas in a csv file with the name given ad argument')
parser.add_argument('-on', 	'--output-nagios',	dest='outputNagios',		action='store_true',		help='print a nagios formatted perfdata output of the selected data')

args = parser.parse_args()

host 		= args.host
community	= args.community
mibFile		= args.mibFile
tableOid	= args.tableOid
verbose 	= args.verbose

columns 	= args.columns
printColumns 	= args.printColumns
printIndexes	= args.printIndexes

outputPrint 	= args.outputPrint
outputCsv	= args.outputCsv
outputNagios	= args.outputNagios


if verbose :
	print('host : {}'.format(host))
	print('community : {}'.format(community))
	print('table : {}::{}'.format(mibFile, tableOid))

if verbose : 
	print('creating snmpTable instace....')
snmpTable = SnmpTable(host, community, '{}::{}'.format(mibFile, tableOid))
if verbose : 
	snmpTable.verbose = True
	print('getting table\'s indexes...')
snmpTable.getIndexes()
if verbose : 
	print('getting table\'s columns')
snmpTable.getColumns()
if verbose : 
	print('done !')

# output process
if snmpTable.isValid :
	if printIndexes :
		print('\n')
		print('SNMP Table indexes : ') 
		snmpTable.listIndexes() 
	if printColumns :
		print('\n')
		print('SNMP Table columns : ') 
		snmpTable.listColumns()
	if len(columns) > 0 :
		for col in columns : 
			snmpTable.getColumnVals(col) 
	else : 
		print('\n')
		snmpTable.getAllVals()
	if outputPrint :		
		snmpTable.displayValues()
	if outputCsv :
		snmpTable.csvValues(outputCsv)
	if outputNagios : 
		snmpTable.nagiosValues()
else : 
	print('Table oid seems to be not found.')

 
