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

parser.add_argument('-H',	'--host', 		dest='host', 			required=True, 			help='The host IP address')
parser.add_argument('-c',	'--community', 		dest='community', 		required=True, 			help='SNMP community')
parser.add_argument('-m',	'--mib-file',		dest='mibFile',			required=True,			help='Mib file of the table')
parser.add_argument('-to',	'--tableOid',		dest='tableOid',		required=True,			help='Table OID String') 	
parser.add_argument('-pc',	'--print-columns',	dest='printColumns',		action='store_true',		help='Print the columns list')
parser.add_argument('-pi', 	'--print-indexes',	dest='printIndexes',		action='store_true',		help='Print the snmp indexes list')
parser.add_argument('-pt',	'--print-table',	dest='printTable',		action='store_true',		help='Print the entire table')
parser.add_argument('-ps',	'--print-selected',	dest='printSelected',		default=[], nargs='*',		help='Print only the columns given in argument')


args = parser.parse_args()

host 		= args.host
community	= args.community
mibFile		= args.mibFile
tableOid	= args.tableOid

snmpTable = SnmpTable(host, community, '{}::{}'.format(mibFile, tableOid))
snmpTable.getIndexes()
snmpTable.getColumns()
if snmpTable.isValid :
	if args.printIndexes :
		print('\n')
		print('SNMP Table indexes : ') 
		snmpTable.listIndexes() 
	if args.printColumns :
		print('\n')
		print('SNMP Table columns : ') 
		snmpTable.listColumns()
	if args.printTable :
		print('\n')
		snmpTable.getAllVals()
		snmpTable.displayValues()
	if len(args.printSelected) > 0 :
		for col in args.printSelected : 
			snmpTable.getColumnVals(col)
		snmpTable.displayValues() 
else : 
	print('Table oid seems to be not found.')

 
