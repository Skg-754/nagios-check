#!/bin/python3

#####################################
#
#   File :          check_omneon-mib.py
#   Description :   
#   Langage :       Python3
#   Date :          
#   Author :        Skg-754
#   
####################################

import subprocess 
import argparse
import re
import os
import json
import sys
import time

# settings the parser
desc='''
'''
parser = argparse.ArgumentParser(description=desc)

parser.add_argument('-H','--host', 		dest='host', 		required=True, 		help='The host IP address')
parser.add_argument('-c','--community', 	dest='community', 	required=True, 		help='SNMP community')
parser.add_argument('-v', '--verbose', 		dest='verbose', 	action='store_true', 	help='Verbose mode')
parser.add_argument('-m', '--mode', 		dest='mode',		required=True,		help='Mode of the script : GENERAL, MEDIADIR, MEDIASTORE')
parser.add_argument('-d', '--device', 		dest='device', 		default='', 		help='Device to check - if empty, check all the devices of the selected mode')

args = parser.parse_args()

# script variables
host = args.host
community = args.community
verbose = args.verbose
mode = args.mode
device = args.device
tmpFilesPrefix = '/tmp/tmp_omneon_{}'.format(host)

devices = {}
players = {}
enclosures = {}
	
infoEventNb = 0
warningEventNb = 0
errorEventNb = 0
criticalEventNb = 0

# # # # # # # # # # 
# NAGIOS VARIABLES
# # # # # # # # # #
nagiosStatusCode = {
	"OK" 		: 0,
	"WARNING" 	: 1,
	"CRITICAL" 	: 2,
	"UNKNOWN" 	: 3
}
statusCode=None
statusInformation=''
perfData=''


def subprocessExec (req) : 
	'''
		Exec a subprocess and return a tuple containing the return code and the return message of the command.
	'''
	# if verbose : 
	#	print(req)
	process = subprocess.Popen(req, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)	
	stdout, stderr = process.communicate()	
	returnMessage = ''
	returnCode = process.returncode
	if process.returncode == 0 :
		returnMessage = stdout
	else :
		statusInformation = 'error on command : {} - {}'.format(req, stderr.decode('utf-8'))
		statusCode = nagiosStatusCode['UNKNOWN']
		print(statusInformation)
		print(perfData)
		sys.exit(statusCode)

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

def omneonSnmpGetExec (array, arrayId, oid, subOid, label) :
	'''
		Exec the snmpGet request en stores the value in the table
	'''
	req = 'snmpget -v 2c -c {} {} {}{} -m OMNEON-MIB'.format(community, host, oid, subOid)
	value = subprocessExec(req)  
	if value[0] != 0 : 
		print('error')
	else : 
		val = snmpgetReturnParser(value[1])	
		array[arrayId][label] = val
# # # # # # # # 
# GENERAL MODE
# # # # # # # #
if mode == 'GENERAL' :

	# # # # # # # # # # #
	# devices analysis
	# # # # # # # # # # #
	req = 'snmpwalk -v 2c -c {} {} omDeviceId -m OMNEON-MIB'.format(community, host)
	devicesSnmpWalk = subprocessExec(req)
	
	if devicesSnmpWalk[0] != 0 : 
		statusInformation = 'snmp error'
		statusCode = nagiosStatusCode['UNKNOWN']
		print(statusInformation)
		print(perfData)
		sys.exit(statusCode)

	else : 
		lines = devicesSnmpWalk[1].split('\n')[:-1]
		for line in lines : 
			deviceId = line[-5:]
			if deviceId.isdigit() :
				devices[deviceId] = {}
				subOid=''
				for char in deviceId : 
					val = ord(char)
					subOid+='.'+str(val)	
				omneonSnmpGetExec (devices, deviceId, "OMNEON-MIB::omDeviceName.5", 		subOid, 'omDeviceName')	
				omneonSnmpGetExec (devices, deviceId, "OMNEON-MIB::omDeviceStatus.5", 		subOid, 'omDeviceStatus')	
				omneonSnmpGetExec (devices, deviceId, "OMNEON-MIB::omDeviceInfoEvents.5", 	subOid, 'omDeviceInfoEvents')	
				omneonSnmpGetExec (devices, deviceId, "OMNEON-MIB::omDeviceWarningEvents.5", 	subOid, 'omDeviceWarningEvents')	
				omneonSnmpGetExec (devices, deviceId, "OMNEON-MIB::omDeviceErrorEvents.5", 	subOid, 'omDeviceErrorEvents')			
				omneonSnmpGetExec (devices, deviceId, "OMNEON-MIB::omDeviceCriticalEvents.5", 	subOid, 'omDeviceCriticalEvents')	
	
		with open('{}_{}'.format(tmpFilesPrefix, 'devices'), 'w') as file :
			file.write(json.dumps(devices))
	
	if verbose :
		print('Information collected on {} devices'.format(len(devices)))
		header = ' {} | {} | {} | {} | {} | {} '.format(
			'omDeviceName'.ljust(20),
			'omDeviceStatus'.ljust(20),
			'Info'.ljust(10),
			'Warning'.ljust(10),
			'Error'.ljust(10),
			'Critical'.ljust(10))
		print(header)
	
		for val in devices.values() : 
			view = ' {} | {} | {} | {} | {} | {} '.format(
				val['omDeviceName'].ljust(20),
				val['omDeviceStatus'].ljust(20),
				val['omDeviceInfoEvents'].ljust(10),
				val['omDeviceWarningEvents'].ljust(10),
				val['omDeviceErrorEvents'].ljust(10),
				val['omDeviceCriticalEvents'].ljust(10))
		
			print(view)
	
	# # # # # # # # # # #
	# enclosure analysis
	# # # # # # # # # # #
	req = 'snmpwalk -v 2c -c {} {} omEnclosureGUID -m OMNEON-MIB'.format(community, host)
	enclosuresSnmpWalk = subprocessExec(req)
	
	if enclosuresSnmpWalk[0] != 0 : 
		statusInformation = 'snmp error'
		statusCode = nagiosStatusCode['UNKNOWN']
		print(statusInformation)
		print(perfData)
		sys.exit(statusCode)

	else : 
		lines = enclosuresSnmpWalk[1].split('\n')[:-1]
		for line in lines :
			enclosureId = line[-16:]
			enclosures[enclosureId] = {}
			subOid=''
			for number in enclosureId :
				val = ord(number)
				subOid+='.'+str(val)		
			omneonSnmpGetExec (enclosures, enclosureId, "OMNEON-MIB::omEnclosureName.16", 		subOid, 'omEnclosureName')	
			omneonSnmpGetExec (enclosures, enclosureId, "OMNEON-MIB::omEnclosureStatus.16", 	subOid, 'omEnclosureStatus')	
			omneonSnmpGetExec (enclosures, enclosureId, "OMNEON-MIB::omEnclosureDirectorName.16", 	subOid, 'omEnclosureDirectorName')	
			omneonSnmpGetExec (enclosures, enclosureId, "OMNEON-MIB::omEnclosureInfoEvents.16",	subOid, 'omEnclosureInfoEvents')	
			omneonSnmpGetExec (enclosures, enclosureId, "OMNEON-MIB::omEnclosureWarningEvents.16",	subOid, 'omEnclosureWarningEvents')			
			omneonSnmpGetExec (enclosures, enclosureId, "OMNEON-MIB::omEnclosureErrorEvents.16",	subOid, 'omEnclosureErrorEvents')			
			omneonSnmpGetExec (enclosures, enclosureId, "OMNEON-MIB::omEnclosureCriticalEvents.16",	subOid, 'omEnclosureCriticalEvents')			
		
		with open('{}_{}'.format(tmpFilesPrefix, 'enclosures'), 'w') as file :
			file.write(json.dumps(enclosures))
	
	if verbose : 
		print('Information collected on {} enclosures'.format(len(enclosures)))
		header = ' {} | {} | {} | {} | {} | {} | {} '.format(
			'omEnclosureName'.ljust(20),
			'omEnclosureStatus'.ljust(20),
			'omEnclosureDirectorName'.ljust(20),
			'Info'.ljust(10),
			'Warning'.ljust(10),
			'Error'.ljust(10),
			'Critical'.ljust(10))
		print(header)
	
		for val in enclosures.values() : 
			view = ' {} | {} | {} | {} | {} | {} | {} '.format(
				val['omEnclosureName'].ljust(20),
				val['omEnclosureStatus'].ljust(20),
				val['omEnclosureDirectorName'].ljust(20),
				val['omEnclosureInfoEvents'].ljust(10),
				val['omEnclosureWarningEvents'].ljust(10),
				val['omEnclosureErrorEvents'].ljust(10),
				val['omEnclosureCriticalEvents'].ljust(10))
			print(view)
	
	
	
	# # # # # # # # # # #
	# palyers analysis
	# # # # # # # # # # #
	req = 'snmpwalk -v 2c -c {} {} omPlayerName -m OMNEON-MIB -On'.format(community, host)
	playersSnmpWalk = subprocessExec(req)
	
	if playersSnmpWalk[0] != 0 : 
		statusInformation = 'snmp error'
		statusCode = nagiosStatusCode['UNKNOWN']
		print(statusInformation)
		print(perfData)
		sys.exit(statusCode)

	else : 
		lines = playersSnmpWalk[1].split('\n')[:-1]
		for line in lines :
			playerId = line.split(' = ')[0].replace('.1.3.6.1.4.1.11141.1.3.1.1.1','')
			players[playerId] = {}
			playerName = line.split(' = ')[1].split(' ')[1]
			players[playerId]['omPlayerName'] = playerName
			omneonSnmpGetExec (players, playerId, "OMNEON-MIB::omPlayerStatus", 		playerId, 'omPlayerStatus')	
			omneonSnmpGetExec (players, playerId, "OMNEON-MIB::omPlayerDirectorName", 	playerId, 'omPlayerDirectorName')	
			omneonSnmpGetExec (players, playerId, "OMNEON-MIB::omPlayerInfoEvents", 	playerId, 'omPlayerInfoEvents')	
			omneonSnmpGetExec (players, playerId, "OMNEON-MIB::omPlayerWarningEvents", 	playerId, 'omPlayerWarningEvents')	
			omneonSnmpGetExec (players, playerId, "OMNEON-MIB::omPlayerErrorEvents", 	playerId, 'omPlayerErrorEvents')	
			omneonSnmpGetExec (players, playerId, "OMNEON-MIB::omPlayerCriticalEvents", 	playerId, 'omPlayerCriticalEvents')	
	
		with open('{}_{}'.format(tmpFilesPrefix, 'players'), 'w') as file :
			file.write(json.dumps(players))
	
	if verbose : 
		print('Information collected on {} players'.format(len(players)))
		header = ' {} | {} | {} | {} | {} | {} | {} '.format(
			'omPlayerName'.ljust(20),
			'omPlayerStatus'.ljust(20),
			'omPlayerDirectorName'.ljust(20),
			'Info'.ljust(10),
			'Warning'.ljust(10),
			'Error'.ljust(10),
			'Critical'.ljust(10))
		print(header)
		for val in players.values() : 	
			view = ' {} | {} | {} | {} | {} | {} | {} '.format(
				val['omPlayerName'].ljust(20),
				val['omPlayerStatus'].ljust(20),
				val['omPlayerDirectorName'].ljust(20),
				val['omPlayerInfoEvents'].ljust(10),
				val['omPlayerWarningEvents'].ljust(10),
				val['omPlayerErrorEvents'].ljust(10),
				val['omPlayerCriticalEvents'].ljust(10))
			print(view)
	
	
	for element in devices.values() :		
		infoEventNb += int(element['omDeviceInfoEvents'])
		warningEventNb += int(element['omDeviceWarningEvents'])
		errorEventNb += int(element['omDeviceErrorEvents'])
		criticalEventNb += int(element['omDeviceCriticalEvents'])
	for element in enclosures.values() :
		infoEventNb += int(element['omEnclosureInfoEvents'])
		warningEventNb += int(element['omEnclosureWarningEvents'])
		errorEventNb += int(element['omEnclosureErrorEvents'])
		criticalEventNb += int(element['omEnclosureCriticalEvents'])	
	for element in players.values() :
		infoEventNb += int(element['omPlayerInfoEvents'])
		warningEventNb += int(element['omPlayerWarningEvents'])
		errorEventNb += int(element['omPlayerErrorEvents'])
		criticalEventNb += int(element['omPlayerCriticalEvents'])
	if warningEventNb == 0 and errorEventNb == 0 and criticalEventNb == 0 : 
		statusCode = nagiosStatusCode['OK']
		statusInformation = '{} ok : {} devices, {} enclosures and {} players checked'.format(host, len(devices), len(enclosures), len(players))	

# # # # # # # # # 
# MEDIADIR MODE
# # # # # # # # #
elif mode == 'MEDIADIR' :
 
	deviceFile = '{}_{}'.format(tmpFilesPrefix, 'devices')
	playerFile = '{}_{}'.format(tmpFilesPrefix, 'players')

	if os.path.isfile(playerFile) :
		fileAge = time.time() - os.path.getmtime(playerFile)
		if fileAge < 120 :
			with open(playerFile) as file :
				players = json.loads(file.read())
		else : 
			statusInformation = 'omneon data older than 2 minutes - check the SNMP settings'
			statusCode = nagiosStatusCode['UNKNOWN']
			print(statusInformation)
			print(perfData)
			sys.exit(statusCode)
	
	else :
		print('devices file not found - run the script in GENERAL mode first')
	activePlayers = 0
	totalPlayers = 0
	for pl in players.values() :	
		if pl['omPlayerDirectorName'] == device :
			totalPlayers += 1
			if verbose : 
				print(pl)
			infoEventNb += int(pl['omPlayerInfoEvents'])				
			warningEventNb += int(pl['omPlayerWarningEvents'])	
			errorEventNb += int(pl['omPlayerErrorEvents'])
			criticalEventNb += int(pl['omPlayerCriticalEvents'])
			
			if warningEventNb > 0 :
				statusInformation = '{} {} has {} warning message'.format(statusInformation, warningEventNb, pl['omPlayerName'])
			if errorEventNb > 0 :
				statusInformation = '{} {} has {} error message'.format(statusInformation,errorEventNb, pl['omPlayerName'])
			if criticalEventNb > 0 :
				statusInformation = '{} {} has {} critical message'.format(statusInformation, criticalEventNb, pl['omPlayerName'])
			if pl['omPlayerStatus'] != 'plrActive(6)' :
				statusInformation = '{} {} status : {},'.format(statusInformation, pl['omPlayerName'], pl['omPlayerStatus'])
				statusCode = nagiosStatusCode['CRITICAL']
			else :
				activePlayers += 1
	perfData = "{} 'totalPlayers'={} 'activePlayers'={}".format(perfData, totalPlayers, activePlayers)
			
	if os.path.isfile(deviceFile) :
		fileAge = time.time() - os.path.getmtime(deviceFile)
		if fileAge < 120 : 
			with open(deviceFile) as file :
				devices = json.loads(file.read())
		else : 
			statusInformation = 'omneon data older than 2 minutes - check the SNMP settings'
			statusCode = nagiosStatusCode['UNKNOWN']
			print(statusInformation)
			print(perfData)
			sys.exit(statusCode)
	
	else :
		print('devices file not found - run the script in GENERAL mode first')
	for dv in devices.values() :
		if dv['omDeviceName'] == device : 
			if verbose : 
				print(dv)
	
			infoEventNb += int(dv['omDeviceInfoEvents'])				
			warningEventNb += int(dv['omDeviceWarningEvents'])	
			errorEventNb += int(dv['omDeviceErrorEvents'])
			criticalEventNb += int(dv['omDeviceCriticalEvents'])
			
			if warningEventNb > 0 :
				statusInformation = '{} {} has {} warning message'.format(statusInformation, dv['omDeviceName'], warningEventNb)
			if errorEventNb > 0 :
				statusInformation = '{} {} has {} error message'.format(statusInformation, dv['omDeviceName'], errorEventNb)
			if criticalEventNb > 0 :
				statusInformation = '{} {} has {} critical message'.format(statusInformation, dv['omDeviceName'], criticalEventNb)
			if dv['omDeviceStatus'] != 'devOkay(1)' :
				statusInformation = '{} {} status : {}, '.format(statusInformation, dv['omDeviceName'], dv['omDeviceStatus'])  
				statusCode = nagiosStatusCode['CRITICAL']
			if statusCode == None : 
				statusCode = nagiosStatusCode['OK']
				statusInformation = '{} {} status : {},'.format(statusInformation, dv['omDeviceName'], dv['omDeviceStatus'])	
# # # # # # # # # # 
# MEDIASTORE MODE
# # # # # # # # # #			
elif mode == 'MEDIASTORE' : 
	enclosuresFile = '{}_{}'.format(tmpFilesPrefix, 'enclosures')
	if os.path.isfile(enclosuresFile) :
		 
		fileAge = time.time() - os.path.getmtime(enclosuresFile)
		if fileAge < 120 : 
			with open(enclosuresFile) as file :
				enclosures = json.loads(file.read())
		else :
			statusInformation = 'omneon data older than 2 minutes - check the SNMP settings'
			statusCode = nagiosStatusCode['UNKNOWN']
			print(statusInformation)
			print(perfData)
			sys.exit(statusCode)
	else :
		print('enclosures file not found - run the script in GENERAL mode first')
	for enc in enclosures.values() :
		if enc ['omEnclosureName'] == device : 
			if verbose : 
				print(enc)
			infoEventNb += int(enc['omEnclosureInfoEvents'])				
			warningEventNb += int(enc['omEnclosureWarningEvents'])	
			errorEventNb += int(enc['omEnclosureErrorEvents'])
			criticalEventNb += int(enc['omEnclosureCriticalEvents'])
		
			if warningEventNb > 0 :
				statusInformation = '{} {} has {} warning message'.format(statusInformation, enc['omEnclosureName'], warningEventNb)
			if errorEventNb > 0 :
				statusInformation = '{} {} has {} error message'.format(statusInformation, enc['omEnclosureName'], errorEventNb)
			if criticalEventNb > 0 :
				statusInformation = '{} {} has {} critical message'.format(statusInformation, enc['omEnclosureName'], criticalEventNb)
			if enc['omEnclosureStatus'] != 'enclOkay(2)' :
				statusCode = nagiosStatusCode['CRITICAL']
			statusInformation = '{} {} status : {}'.format(statusInformation, enc['omEnclosureName'], enc['omEnclosureStatus'])  
			if statusCode == None : 
				statusCode = nagiosStatusCode['OK']


else :
	print('unknown mode')

if statusCode == None :
	statusCode = nagiosStatusCode['UNKNOWN']
if statusInformation == '' : 
	statusInformation = 'no informations'


if warningEventNb > 0 :
	statusCode = nagiosStatusCode['WARNING']
if errorEventNb > 0 :
	statusCode = nagiosStatusCode['CRITICAL']
if criticalEventNb > 0 :
	statusCode = nagiosStatusCode['CRITICAL']

perfData = "{} 'info'={} 'warning'={} 'error'={} 'critical'={}".format(perfData, infoEventNb, warningEventNb, errorEventNb, criticalEventNb)



# nagios output
print('{} | {}'.format(statusInformation, perfData))
sys.exit(statusCode)
