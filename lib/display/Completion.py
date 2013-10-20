# coding=utf8

import re
import json
from ..Utils import get_prefix

class Completion(object):

	completion_list = []
	interface = False
	enabled = False

	def set_interface_completion(self,value):
		self.interface = value

	def prepare_list(self,data):
		del self.completion_list[:]

		try:
			entries = json.loads(data)['entries']
		except:
			print('completion json error : ',data)
			return
		
		for entry in entries:
			if self.interface and entry['kind'] != 'primitive type' and entry['kind'] != 'interface' : continue
			key = self.get_list_key(entry)
			value = self.get_list_value(entry)
			self.completion_list.append((key,value))

		self.completion_list.sort()


	def get_list_key(self,entry):
		kindModifiers = get_prefix(entry['kindModifiers'])
		kind = get_prefix(entry['kind'])

		return kindModifiers+' '+kind+' '+str(entry['name'])+' '+str(entry['type'])


	def get_list_value(self,entry):
		match = re.match('(<.*>|)\((.*)\):',str(entry['type']))
		result = []

		if match:
			variables = self.parse_args(match.group(2))
			count = 1
			for variable in variables:
				splits = variable.split(':')
				if len(splits) > 1:
					data = '"'+variable+'"'
					data = '${'+str(count)+':'+data+'}'
					result.append(data)
					count = count+1
				else:
					result.append('')

			return entry['name']+'('+','.join(result)+');'
		else:
			return entry['name']


	def parse_args(self,group):
		args = []
		arg = ""
		callback = False

		for char in group:
			if char == '(':
				arg += char
				callback = True
			elif char == ')':
				arg += char
				callback = False
			elif char == ',':
				if callback == False:
					args.append(arg)
					arg = ""
			else:
				arg+=char

		args.append(arg)
		return args

		
	def get_list(self):
		return self.completion_list


COMPLETION = Completion()