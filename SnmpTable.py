from utils import processExec, parseSnmpSingleResult


class SnmpTable :
	'''
	'''
	def __init__(self, host, community, tableOid) :
		'''
		'''
		self.host = host
		self.community = community
		self.tableOid = tableOid
		
		self.indexes = []
		# transform tableOid innumercialOId
		request = 'snmptranslate -On {}'.format(self.tableOid)
		returnCode, returnMessage = processExec(request)
		if returnCode != 0 : 
			print('error')
		else : 
			self.numericalOid = returnMessage.replace('\n', '')

	def getIndexes (self) :
		'''
		'''
		request = 'snmpwalk -v 2c -c {} {} {}.1.1'.format(self.community, self.host, self.tableOid)
		returnCode, returnMessage = processExec(request)
		if returnCode != 0 :
			print('error')
		else : 
			lines = returnMessage.split('\n')[:-1]
			for line in lines :
				result = parseSnmpSingleResult(line) 
				self.indexes.append(result['index'])

	
	def listIndex (self) : 
		'''
		'''
		for index in self.indexes : 
			print(index)

	def getColumns (self) :
		'''
		'''
		crtColumn = 0
		def loop (crtColumn) :
			request = 'snmpgetnext -v 2c -On -c {} {} {}.1.{}'.format(self.community, self.host, self.tableOid, crtColumn)
			returnCode, returnMessage = processExec(request)
			if returnCode != 0 :
				print('error')
			else : 
				result = parseSnmpSingleResult(returnMessage)
				print(self.numericalOid)
				print(result['columnOid'])
				if self.numericalOid in result['columnOid'] :
					crtColumn+=1
					

					request = 'snmptranslate -To {}'.format(result['columnOid'])
					print(request)
					returnCode, returnMessage = processExec(request)
					print(returnMessage)
					loop(crtColumn)
		loop(crtColumn)

	
