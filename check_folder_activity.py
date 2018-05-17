#!/bin/python3

#####################################
#
#   File :          check_folder_active.py
#   Description :   Nagios plugin to check if files are being updated in a directory
#   Langage :       Python3
#   Date :          2018-05-09
#   Author :        Skg-754
#
#   This plugin uses the wmic command to query a list of the last edited files in a remote directory.
#   The commands is executed twice. If the results of the two request are the same, the folder is considered as not active. 
#
#####################################


import subprocess 
import argparse
import datetime
import sys

# setting the parser

desc='''
	This plugin uses the wmic command to query a list of the last edited files in a directory.
	The commands is executed twice. If the results of the two request are the same, the folder is considered as not active.
	PerfData out : 1 = modifications detected, -1 = no modifications detected, 0 = wmi error or file not found 
'''

parser = argparse.ArgumentParser(description=desc)

parser.add_argument('-d','--drive', 	dest='drive', 		default='C:', 		help='The hard drive letter on which is stored the folder to check')
parser.add_argument('-a','--auth-file', dest='authFile', 	required=True, 		help='The authentication file for the wmi connection')
parser.add_argument('-H','--host', 	dest='host', 		required=True, 		help='The host IP address')
parser.add_argument('-p', '--path', 	dest='path',  		required=True, 		help='The path to the folder to check (unix style)')
parser.add_argument('-t', '--delta', 	dest='delta', 		type=int, default=0, 	help='Delta time in minutes beyond wich files are not analyzed - Used to limit the number of result of the wmi request')
parser.add_argument('-s', '--shortcut', dest='shortcut', 	default=False,		help='To use only if shortcut file is used to access the folder. Name of the shortcut file')
parser.add_argument('-v', '--verbose', 	dest='verbose', 	action='store_true', 	help='Verbose mode')


args = parser.parse_args()


def pathFormatter (myPath) :	
	'''
		Transform unix style path into windows style path
	'''
	return myPath.replace('/','\\\\')


# user arguments
drive=args.drive			# drive where is stored the folder to checke
authFile=args.authFile			# authentication file for the wmi connection
host=args.host				# host IP address
path=pathFormatter(args.path) 		# path (UNIX style)
delta=args.delta			# relative time range for file search in minutes
verbose=args.verbose			# verbose mode
shortcut=args.shortcut			# name of the shortcut file of the folder (default = false)

userFriendlyPath = args.path

# date - used for limit the number of result
searchDate=datetime.datetime.now()-datetime.timedelta(minutes=delta)
formattedSearchDate=searchDate.strftime('%Y%m%d%H%M%S')

# nagios output ini
nagiosStatusCode = {
	"OK" 		: 0,
	"WARNING" 	: 1,
	"CRITICAL" 	: 2,
	"UNKNOWN" 	: 3
}
statusCode=None
statusInformation=None
perfData=None

# if a shortcut file is used
if shortcut :
	request = 'wmic -A {} //{} \'Select Target FROM Win32_ShortcutFile WHERE Drive="{}" and Path="{}" and FileName="{}"\''.format(authFile, host, drive, path, shortcut)
	if verbose : 
		print(request)
	result = subprocess.Popen(request, shell=True, stdout=subprocess.PIPE).stdout.read()
	resultArray = str(result).split('|')
	if len(resultArray) == 3 :
		fullPath = resultArray[-1]
		if verbose :
			print(fullPath)
		drive = fullPath[0:2]
		path = fullPath[2:-3]+'\\\\'
		userFriendlyPath = path.replace('\\\\','/')
	else : 
		statusInformation = 'Error : Shortcut file not found or WMI error'
		perfData = "'isActive'=0"
		statusCode = nagiosStatusCode['UNKNOWN']
		
		# nagios output
		print('{} | {}'.format(statusInformation, perfData))
		sys.exit(statusCode)
	
	

# wmi command
request = 'wmic -A {} //{} \'Select LastModified FROM CIM_DataFile WHERE Drive="{}" AND Path="{}" and LastModified>"{}.000000+000"\''.format(authFile, host, drive, path, formattedSearchDate)

if verbose :
	print('drive : {} - authFile : {} - host : {} - path : {} - delta : {}'.format(drive, authFile, host, path, delta))
	print(request)

# execution of the wmi command for the first time
result1 = subprocess.Popen(request, shell=True, stdout=subprocess.PIPE).stdout.read()

if verbose : 
	print(result1)

# execution of the wmi command for the second time
result2 = subprocess.Popen(request, shell=True, stdout=subprocess.PIPE).stdout.read()

if verbose :
	print(result2)

# comparison of the two results
if result1 == result2 :	
	if str(result1).find('ERROR: Retrieve result data.') : 
		statusInformation = 'WMI error, unable to request the folder : {}'.format(str(result1))
		perfData = "'isActive'=0"
		statusCode = nagiosStatusCode['UNKNOWN']
	else :
		statusInformation = 'No changes detected in the folder : {}'.format(userFriendlyPath)
		perfData = "'isActive'=-1"
		statusCode = nagiosStatusCode['CRITICAL']
else :
	statusInformation = 'Changes detected in the folder {}'.format(userFriendlyPath)
	perfData = "'isActive'=1"
	statusCode = nagiosStatusCode['OK']
	

# nagios output
print('{} | {}'.format(statusInformation, perfData))
sys.exit(statusCode)




