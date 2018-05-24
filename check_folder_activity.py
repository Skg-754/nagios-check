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



def wmiErrorAnalysis (stderr) :
	'''
		Analysis of the stderr of a wmi command
		Extract the error code and give the error descr
		:param sdterr:	the binary stderr message
		:return: a tuple containing the error code and the error descr
	'''

	# wmi errors
	wmiErrors = {
		'0x8007000e' : 'Not enough storage is available to complete this operation',
		'0x80010108' : 'The object invoked has disconnected from its clients.',
		'0x800705af' : 'The paging file is too small for this operation to complete.',
		'0x80010111' : 'Unknown error',
		'0xc002001b' : 'WMI Timeout error',
		'0x80041013' : 'Provider Load Failure'
	}	

	errorCode = stderr.decode('utf-8')[18:28]
	errorMsg = 'Unkown error'
	if errorCode in wmiErrors.keys() :
		errorMsg = wmiErrors[errorCode]
	
	return errorCode, errorMsg


def wmiCommandExec (request) :
	'''
		Try to execute a wmi command
		If subprocess return an error code, exit the script and
		Else, return the sdtout of the command
	'''
	if verbose :
		print(request)
	process = subprocess.Popen(request, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()

	if process.returncode != 0 :
		if verbose :
			print('wmic command return and error return code')
		errorCode, errorMsg = wmiErrorAnalysis(stderr)
		statusInformation = 'WMI Error : {} - {}'.format(errorCode, errorMsg)
		perfData = "'isActive'=0"
		statusCode = nagiosStatusCode['UNKNOWN']

		# nagios output - end of script
		print('{} | {}'.format(statusInformation, perfData))
		sys.exit(statusCode)
	else : 
		return stdout
		
	

# if a shortcut file is used
if shortcut :
	request = 'wmic -A {} //{} \'Select Target FROM Win32_ShortcutFile WHERE Drive="{}" and Path="{}" and FileName="{}"\''.format(authFile, host, drive, path, shortcut)
	
	stdout = wmiCommandExec(request) 
	resultArray = stdout.decode('utf-8').split('|')
 
	if len(resultArray) == 3 :	
		fullPath = resultArray[-1]
		if verbose :
			print(fullPath)
		drive = fullPath[0:2]
		path = fullPath[2:-1].replace('\\','\\\\')+'\\\\'
		userFriendlyPath = path.replace('\\\\','/')
	else : 
		firstResult = resultArray[0]
		statusInformation = 'Error : Shortcut file not found'
		perfData = "'isActive'=0"
		statusCode = nagiosStatusCode['UNKNOWN']
	
		# nagios output - end of script
		print('{} | {}'.format(statusInformation, perfData))
		sys.exit(statusCode)
	
	

# wmi command 
request = 'wmic -A {} //{} \'Select LastModified FROM CIM_DataFile WHERE Drive="{}" AND Path="{}" and LastModified>"{}.000000+000"\''.format(authFile, host, drive, path, formattedSearchDate)

if verbose :
	print('drive : {} - authFile : {} - host : {} - path : {} - delta : {}'.format(drive, authFile, host, path, delta))
	print(request)

# request 1
result1 = wmiCommandExec(request)
if verbose : 
	print(result1.decode('utf-8'))

# request 2
result2 = wmiCommandExec(request)
if verbose :
	print(result2.decode('utf-8'))

# comparison of the two results
if result1 == result2 :	
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




