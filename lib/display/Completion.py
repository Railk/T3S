# coding=utf8

import re
import json
import sublime
from ..Utils import get_prefix, is_member_completion, get_file_infos, Debug


class Completion(object):

	completion_chars = ['.']#['.',':']
	completion_list = []
	interface = False
	enabled = False

	# PREPARE LISTE
	def prepare_list(self, tss_result_json):
		del self.completion_list[:]

		try:
			entries = json.loads(tss_result_json)['entries']
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
	def trigger(self, view, TSS, force_enable=False):
		pos = view.sel()[0].begin()
		(line, col) = view.rowcol(pos)
		char = view.substr(pos-1)
		
		self.enabled = force_enable or char in self.completion_chars
		self.interface = char is ':'

		if self.enabled:

			def get_content_of_line_at(view, pos):
				return view.substr(sublime.Region(view.line(pos-1).a, pos))
	
			is_member = is_member_completion( get_content_of_line_at(view, pos) )
			is_member = str( is_member ).lower()
			
			TSS.update(*get_file_infos(view))
			
			def async_react_completions_available(tss_result_json):
				COMPLETION.prepare_list(tss_result_json)
			
				# this will trigger Listener.on_query_completions 
				# but on_query_completions needs to have the completion list
				# already available
				view.run_command('auto_complete',{
					'disable_auto_insert': True,
					'api_completions_only': True,
					'next_completion_if_showing': True
				})
			
			TSS.complete(view.file_name(), line, col, is_member, async_react_completions_available)

			


	# ENTRY KEY
	def _get_list_key(self,entry):
		kindModifiers = get_prefix(entry['kindModifiers'])
		kind = get_prefix(entry['kind'])
		type = entry['type'] if 'type' in entry else entry['name']

		return kindModifiers+' '+kind+' '+str(entry['name'])+' '+str(type)


	# ENTRY VALUE
	def _get_list_value(self,entry):
		type = entry['type'] if 'type' in entry else entry['name']
		match = re.match('(<.*>|)\((.*)\):',str(type))
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

			return re.escape(entry['name'])+'('+','.join(result)+')'
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
