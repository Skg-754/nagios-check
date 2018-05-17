#!/bin/python3

####################################
#
#   File : 	    check_ipmi_simple.py
#   Description :   Nagios check script to check ipmi sensors
#   Langage :       Python3
#   Date :	    2018-05-17
#   Author :        Skg-754
#
#####################################


import subprocess
import argparse
import os.path
import sys

desc='''
	Nagios script to check ipmi sensors 
	Depedencies : ipmitool
'''

parser = argparse.ArgumentParser(description=desc)

parser.add_argument('-H',	'--host',      	dest='host',            required=True,          help='The host IP address')
parser.add_argument('-u',	'--user', 	dest='user',		default='',		help='IPMI username')
parser.add_argument('-p',	'--password',	dest='password',	default='',		help='IPMI password')
parser.add_argument('-c',	'--credFile',	dest='credFile',	default='',		help='Credential file')
parser.add_argument('-s',	'--sensors',	dest='sensors',		default=[], nargs='*',	help='List of the sensors to check. If not set, all sensors are checked')
parser.add_argument('-v',	'--verbose',  	dest='verbose',         action='store_true',    help='Verbose mode')

args = parser.parse_args()

# user arguments
host = args.host
user = args.user
password = args.password
credFile = args.credFile
sensors = args.sensors
verbose = args.verbose


# nagios output ini
nagiosStatusCode = {
        "OK"            : 0,
        "WARNING"       : 1,
        "CRITICAL"      : 2,
        "UNKNOWN"       : 3
}
statusCode=3
statusInformation=''
perfData=''

# checking credentialsi
if credFile != '' and user != '' :
	print('Choose either ser and password (-u or -p) or credential file (-c)')
	sys.exit(statusCode)
elif credFile == '' and user == '' : 
	print('Either user and password (-u or -p) or credential file (-c) is required')
	sys.exit(statusCode)
elif credFile != '' :
	if os.path.isfile(credFile) :	
		creds = open(credFile).readlines()
		result = []
		for line in creds :
			result.append(line.rstrip('\n').split('='))
		if result[0][0] == 'username' and result[1][0] == 'password' :
			user=result[0][1]
			password=result[1][1]
		else : 
			print('AuthFile parsing error')
			sys.exit(statusCode)
	else :
		print('AuthFile not found')
		sys.exit(statusCode)


# gettings ipmi informations

request = 'ipmitool -I lanplus -H {} -U {} -P {} sensor list'.format(host, user, password)
if verbose : 
	print(request)

result = subprocess.Popen(request, shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8')
if verbose : 
	print(result)
result = result.split('\n')[:-1]


if len(result) > 0 :
	statusCode = 0

resultTable = {}
for sensor in result : 
	sensorValues = sensor.split('|')
	sensorName = sensorValues[0].strip()
	sensorValue = sensorValues[1].strip() 
	sensorUnit = sensorValues[2].strip()
	sensorState = sensorValues[3].strip()
	resultTable[sensorName] = { 'name' : sensorName, 'value' : sensorValue,'unit' : sensorUnit, 'state' : sensorState }

def checkState (sensor) :
	statusCode = False
	perfData = ''
	statusInformation = ''
	unit = sensor['unit']
	name = sensor['name']
	value = sensor['value']
	state = sensor['state']
	if state == 'na' :
		statusCode = nagiosStatusCode['CRITICAL']
		statusInformation += '{} : no data available'.format(name)
		perfData += "'{}'=-1".format(name)
	else :
		if unit == 'Volts' :
			print('not supported')	
		elif unit == 'degrees C' :  
			perfData += "'{}'={}".format(name, value)
		elif unit == 'discrete' : 
			if value == '0x1' : # success	
				perfData += "'{}'=1".format(name)
			else : # error
				statusCode = nagiosStatusCode['CRITICAL']
				statusInformation += '{} : nok'.format(name)
				perfData +=  "'{}'=-1".format(name)
		elif unit == 'RPM' :
			if state == 'ok' :    
				perfData += "'{}'={}".format(name, value)
			else :
				statusCode = nagiosStatusCode['CRITICAL']
				statusInformation += '{} : nok'.format(name)
				perfData += "'{}'=-1".format(name)
		elif unit == 'na' :
				statusCode = nagiosStatusCode['CRITICAL']
				statusInformation += '{} : no data available'.format(name)
				perfData += "'{}'=-1".format(name)
		else : 
			print(unit + ' not supported')

	return (statusCode, statusInformation, perfData)


if len(sensors)>0 : 
	for sensorName in sensors :		
		code, status, perf = checkState(resultTable[sensorName])
		if code : 
			statusCode = code
		if status != '' : 
			statusInformation += ' '+status
		perfData += ' '+perf

if statusCode == 0 :
	statusInformation = 'OK ' + statusInformation
elif statusCode == 1 :
	statusInformation = 'WARNING ' + statusInformation
elif statusCode == 2 :
	statusInformation = 'CRITICAL ' + statusInformation
elif statusCode == 3 :
	statusInformation  = 'UNKNOWN ' + statusInformation

print(statusInformation + ' |' + perfData)
sys.exit(statusCode)





