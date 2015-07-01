# coding=utf8

import re
import json
import sublime
from ..Utils import get_prefix, is_member_completion, \
	 get_file_infos, Debug, get_col_after_last_dot, get_content_of_line_at


class Completion(object):

	completion_chars = ['.']#['.',':']
	completion_list = []
	interface = False
	enabled_for_col_reference = '' 	# 'dot' or 'cursor'
	enabled_for = {'line': 0, 'col': 0, 'viewid': -1}

	# PREPARE LISTE
	def prepare_list(self, tss_result_json):
		del self.completion_list[:]

		try:
			entries = json.loads(tss_result_json)['entries']
		except:
			if tss_result_json.strip() == 'null':
				sublime.status_message('T3S: no completions available')
			else:
				print('completion json error : ', tss_result_json)
			return 0
		
		for entry in entries:
			if self.interface and entry['kind'] != 'primitive type' and entry['kind'] != 'interface' : continue
			key = self._get_list_key(entry)
			value = self._get_list_value(entry)
			self.completion_list.append((key,value))

		self.completion_list.sort()
		return len(self.completion_list)


	# GET LISTE
	def get_list(self):
		return self.completion_list


	# TYPESCRIPT COMPLETION ?
	def trigger(self, view, TSS, force_enable=False):

		cursor_pos = view.sel()[0].begin() # cursor pos as int
		(cursor_line, cursor_col) = view.rowcol(cursor_pos)

		char = view.substr(cursor_pos-1)
		

		enabled = force_enable or (char in self.completion_chars)
		self.interface = char is ':'

		if enabled:
			Debug('autocomplete', "Autocompletion for line %i , %i, forced=%s" % (cursor_line+1, cursor_col+1, force_enable) )
	
			is_member = is_member_completion( get_content_of_line_at(view, cursor_pos) )
			is_member_str = str( is_member ).lower() # 'true' or 'false'

			# do execute tss.js complete for cursor positon after last dot, so we use 
			# sublimes fuzzy mechanism to reduce the list, not the mechanism
			# (1:1 matching of the typed chars) tss.js would use

			autocomplete_col = 0

			if is_member:
				autocomplete_col = get_col_after_last_dot( get_content_of_line_at(view, cursor_pos) )
				self.enabled_for_col_reference = 'dot'
				if autocomplete_col != cursor_col:
					Debug('autocomplete', " -> dot is on col %i, use this col instead of cursor position %i" % (autocomplete_col+1, cursor_col+1))
			else:
				Debug('autocomplete', " -> use cursor position %i for autocomplete" % (cursor_col+1))
				self.enabled_for_col_reference = 'cursor'
				autocomplete_col = cursor_col

			self.enabled_for['viewid'] = view.id()
			self.enabled_for['line'] = cursor_line
			self.enabled_for['col'] = autocomplete_col
			
			Debug('autocomplete', " -> push current file contents as update to tss.js")
			TSS.update(*get_file_infos(view))
			
			def async_react_completions_available(tss_result_json, filename, line, col, is_member_str):
				Debug('autocomplete', "Autocompletion results available for line %i , %i" % (line+1, col+1) )

				i = COMPLETION.prepare_list(tss_result_json)
				Debug('autocomplete', " -> prepare List (%i items)" % i )

				# view or line changed
				current_view = sublime.active_window().active_view()
				current_cursor_pos = current_view.sel()[0].begin()
				(current_cursor_line, current_cursor_col) = current_view.rowcol(current_cursor_pos)

				if current_view.id() != self.enabled_for['viewid'] or filename != current_view.file_name():
					Debug('autocomplete', " -> file changed since activation of autocomplete or out-dated request -> cancel")
					return
				if current_cursor_line != self.enabled_for['line'] or current_cursor_line != line:
					Debug('autocomplete', " -> line changed since start of autocomplete (%i to %i) or out-dated request -> cancel" % (current_cursor_line, line) )
					return
				if self.enabled_for_col_reference == 'cursor' \
					and (current_cursor_col != self.enabled_for['col'] or current_cursor_col != col):
					Debug('autocomplete', " -> cursor changed position (current col: %i ; at command issue: %i) or out-dated request -> cancel" % (current_cursor_col, col) )
					return

				if is_member_str == 'true':
					current_dot_col = get_col_after_last_dot( get_content_of_line_at(view, current_cursor_pos) )
					if self.enabled_for_col_reference == 'dot' \
						and (current_dot_col != self.enabled_for['col'] or current_dot_col != col):
						Debug('autocomplete', " -> it's not the same dot reference anymore (current dot pos: %i ; at command issue: %i) or out-dated request -> cancel" % (current_dot_col, col) )
						return


				Debug('autocomplete', " -> command to sublime to now show autocomplete box with prepared list" )

				# this will trigger Listener.on_query_completions 
				# but on_query_completions needs to have the completion list
				# already available
				current_view.run_command('auto_complete',{
					'disable_auto_insert': True,
					'api_completions_only': True,
					'next_completion_if_showing': True
				})
				Debug('autocomplete', " -> (sublime cmd finished)" )
			
			TSS.complete(view.file_name(), cursor_line, autocomplete_col, is_member_str, async_react_completions_available)

			


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
