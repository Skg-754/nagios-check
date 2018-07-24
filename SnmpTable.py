from utils import processExec, parseSnmpSingleResult
import os

class SnmpTable :
	'''
	
	'''
	def __init__(self, host, community, tableOid) :
		'''
		Required arguments : snmp host, snmp community, table oid on format mibFile::TableName
		'''
		self.host = host						# snmp host
		self.community = community					# snmp community
		self.tableOid = tableOid					# table string oid on format mibFile::TableName
		self.isValid = False						# variable set to true if the oid string is found
		self.columns = []						# columns names of the snmp table
		self.mib = None							# the mib file name 
		self.indexes = []						# the indexes of the snmp table
		self.values = {}						# the values collected from the snmp table
		self.verbose = False						# if set to true, print the requests sended to the snmp host
		
		# transform tableOid in numercialOId	
		request = 'snmptranslate -On {}'.format(self.tableOid)
		if self.verbose : 
			print(request)	
		returnCode, returnMessage = processExec(request)
		if returnCode != 0 : 
			print('Error while checking the snmp table oid string.')
		else : 
			self.isValid = True
			self.numericalOid = returnMessage.replace('\n', '')

	def getIndexes (self) :
		'''
		Collect the table indexes and store it the indexes array
		'''
		request = 'snmpwalk -v 2c -c {} {} {}.1.1'.format(self.community, self.host, self.tableOid)
		if self.verbose : 
			print(request)
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
		Print the indexes list
		'''
		for index in self.indexes : 
			print(index)

	def getColumns (self) :
		'''
		Collect columns names and stores it in the columns array
		'''
		crtColumn = 1
		def loop (crtColumn) :
			request = 'snmpgetnext -v 2c -On -c {} {} {}.1.{}'.format(self.community, self.host, self.tableOid, crtColumn)
			if self.verbose : 
				print(request)
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
		Prin the columns name list
		'''
		for column in self.columns : 
			print(column)

	def getColumnVals (self, column) : 
		'''
		Collect the values for a specific column and store it in the values table
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
		'''
		Collect the values of all columns
		'''
		for col in self.columns : 
			self.getColumnVals(col)	

	def getCollectedValues (self) : 
		'''
		Return the collected values array
		'''
		return self.values

	def displayValues (self) : 
		'''
		Print the collected values in a formatted array
		'''
		headers= list(list(self.values.values())[0].keys())
		
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

	def csvValues (self, fileName) :
		'''
		Export de values to a csv file
		'''
		headers= list(list(self.values.values())[0].keys());
		valuesList = list(self.values.values())
		
		csvFile = open(fileName, 'w')
			
		# building the header
		headerString = ''
		for header in headers :
			headerString = '{}{};'.format(headerString, header)
		if self.verbose :
			print(headerString)
		csvFile.write(headerString+os.linesep)

		# writing the datas
				
		for value in valuesList : 
			line = ''
			for key,val in value.items() :
				line = '{}{};'.format(line, val)
			if self.verbose :	
				print(line)	
			csvFile.write(line+os.linesep)

	def nagiosValues (self) : 
		'''
		Export values as nagios perfdata output
		'''
		perfData = 'TablePerfData | '
		headers= list(list(self.values.values())[0].keys())
		for key,data in self.values.items() : 
			for oid,val in data.items() :
				perfData = "{} '{}_{}'='{}'".format(perfData, oid,key,val) 
		print(perfData)
		


