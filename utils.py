import subprocess


def processExec (request) :

	process = subprocess.Popen(request, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()
	returnMessage = ''
	returnCode = process.returncode
	if returnCode == 0 :
		returnMessage = stdout.decode('utf-8')
	else :
		returnMessage = stderr.decode('utf-8')
	return returnCode, returnMessage

def parseSnmpSingleResult(message) :
	message = message.replace('\n','')
	result = {}
	result['columnOid'] 	= message.split(' = ')[0].split('.')
	if len(result['columnOid']) > 2 :
		result['columnOid']     = message.split(' = ')[0]
	else :
		result['columnOid'] = result['columnOid'][0]
	result['index']         = message.split(' = ')[0].split('.').pop()
	result['valueType']     = message.split(' = ')[1].split(': ')[0]
	result['value']         = message.split(' = ')[1].split(': ')[1]
	return result

