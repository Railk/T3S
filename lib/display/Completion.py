# coding=utf8

import re
import json
from ..Utils import get_prefix


class Completion(object):

	completion_chars = ['.',':']
	completion_list = []
	interface = False
	enabled = False

	# PREPARE LISTE
	def prepare_list(self,data):
		del self.completion_list[:]

		try:
			entries = json.loads(data)['entries']
		except:
			print('completion json error : ',data)
			return
		
		for entry in entries:
			if self.interface and entry['kind'] != 'primitive type' and entry['kind'] != 'interface' : continue
			key = self._get_list_key(entry)
			value = self._get_list_value(entry)
			self.completion_list.append((key,value))

		self.completion_list.sort()


	# GET LISTE
	def get_list(self):
		return self.completion_list


	# TYPESCRIPT COMPLETION ?
	def show(self,view,enable=False):
		char  = view.substr(view.sel()[0].begin()-1)
		self.enabled = enable if enable else char in self.completion_chars
		self.interface = char == ':'

		if self.enabled: 
			view.run_command('auto_complete',{
				'disable_auto_insert': True,
				'api_completions_only': True,
				'next_completion_if_showing': True
			})


	# ENTRY KEY
	def _get_list_key(self,entry):
		kindModifiers = get_prefix(entry['kindModifiers'])
		kind = get_prefix(entry['kind'])

		return kindModifiers+' '+kind+' '+str(entry['name'])+' '+str(entry['type'])

	# ENTRY VALUE
	def _get_list_value(self,entry):
		match = re.match('(<.*>|)\((.*)\):',str(entry['type']))
		result = []

		if match:
			variables = self._parse_args(match.group(2))
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

			return re.escape(entry['name'])+'('+','.join(result)+');'
		else:
			return re.escape(entry['name'])

	# PARSE FUNCTION ARGUMENTS
	def _parse_args(self,group):
		args = []
		arg = ""
		callback = False

		for char in group:
			if char == '(' or char == '<':
				arg += char
				callback = True
			elif char == ')' or char == '>':
				arg += char
				callback = False
			elif char == ',':
				if callback == False:
					args.append(arg)
					arg = ""
				else:
					arg+=char	
			else:
				arg+=char

		args.append(arg)
		return args


COMPLETION = Completion()
