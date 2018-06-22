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
		self.isValid = False
		self.columns = []
		self.mib = None	
		self.indexes = []
		self.values = {}
		# transform tableOid innumercialOId
		request = 'snmptranslate -On {}'.format(self.tableOid)
		returnCode, returnMessage = processExec(request)
		if returnCode != 0 : 
			print('Error while checking the snmp table oid string.')
		else : 
			self.isValid = True
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

	
	def listIndexes (self) : 
		'''
		'''
		for index in self.indexes : 
			print(index)

	def getColumns (self) :
		'''
		'''
		crtColumn = 1
		def loop (crtColumn) :
			request = 'snmpgetnext -v 2c -On -c {} {} {}.1.{}'.format(self.community, self.host, self.tableOid, crtColumn)
			returnCode, returnMessage = processExec(request)
			if returnCode != 0 :
				print('error')
			else : 
				result = parseSnmpSingleResult(returnMessage)
				if self.numericalOid in result['columnOid'] :
					crtColumn+=1
					request = 'snmptranslate -To {}'.format(result['columnOid'])
					returnCode, returnMessage = processExec(request)
					strOid = returnMessage.split('\n')[0].split('.')[:-1][0]
					if self.mib == None :
						self.mib = strOid.split('::')[0]
					self.columns.append(strOid.split('::')[1])	
					loop(crtColumn)
		loop(crtColumn)

	def listColumns (self) :
		'''
		'''
		for column in self.columns : 
			print(column)

	def getColumnVals (self, column) : 
		'''
		'''
		request = 'snmpwalk -v 2c -c {} {} {}::{}'.format(self.community, self.host, self.mib, column)
		returnCode, returnMessage = processExec(request)
		if returnCode != 0 : 
			print('error()')
		else :
			lines = returnMessage.split('\n')[:-1]
			for line in lines :
				result = parseSnmpSingleResult(line)
				
				index = result['index']
				if not index in self.values.keys() :
					self.values[index] = {}
				self.values[index][result['columnOid'].split('::')[1]] = result['value'] 

	
	def getAllVals (self) :
		for col in self.columns : 
			self.getColumnVals(col)	

	def getCollectedValues (self) : 
		return self.values

	def displayValues (self) : 
		headers= list(list(self.values.values())[0].keys());
		
		valuesList = list(self.values.values())
		columnsWidth = {}
		for header in headers : 
			columnsWidth[header] = len(header)	
			
		# getting the columns widths
		for value in valuesList :
			for key,val in value.items() : 
				if columnsWidth[key] < len(val) : 
					columnsWidth[key] = len(val)
		# building the header
		headerString = '|'
		for header in headers :
			header = header.ljust(columnsWidth[header])
			headerString = '{} {} |'.format(headerString, header)

		# building line
		print(''.ljust(len(headerString),'-'))

		print(headerString)
	
		# building line
		print(''.ljust(len(headerString),'-'))
		
		# building the data linesi
		for value in valuesList : 
			line = '|'
			for key,val in value.items() :
				val = val.ljust(columnsWidth[key])
				line = '{} {} |'.format(line, val)	
			print(line)	
		
		# building line
		print(''.ljust(len(headerString),'-'))

