# coding=utf8

import sublime
import json
import hashlib

from .display.Completion import COMPLETION
from .display.Message import MESSAGE
from .system.Processes import PROCESSES, AsyncCommand
from .system.Liste import LISTE
from .Utils import is_dts, encode


# --------------------------------------- TSS -------------------------------------- #

class Tss(object):




	# GET PROCESS
	def get_process(self,filename):
		return PROCESSES.get(LISTE.get_root(filename))


	# INIT ROOT FILE
	def init(self,root):
		PROCESSES.add(root, self.notify)
		self.added_files = {}
		self.executed_with_most_recent_file_contents = []


	# RELOAD PROCESS
	def reload(self,filename):
		AsyncCommand('reload\n', None, 'reload').append_to_global_queue(filename)
		self.errors(filename)	

	# GET INDEXED FILES
	def files(self, filename, callback):
		AsyncCommand('files\n', lambda async_command: callback(json.loads(async_command.result)) ) \
			.append_to_global_queue(filename)
		

	# DUMP FILE (untested)
	def dump(self, filename, output, callback):
		dump_command = 'dump {0} {1}\n'.format( output, filename.replace('\\','/') )
		AsyncCommand(dump_command, lambda async_command: callback(async_command.result) ) \
			.append_to_global_queue(filename)

	# TYPE
	def type(self, filename, line, col, callback):
		type_command = 'type {0} {1} {2}\n'.format( str(line+1), str(col+1), filename.replace('\\','/') )
		AsyncCommand(type_command, \
			lambda async_command: callback(json.loads(async_command.result), **async_command.payload ),
			_id="type_command" \
			).add_payload(filename=filename, line=line, col=col) \
			.append_to_global_queue(filename)

	# DEFINITION
	def definition(self, filename, line, col, callback):
		definition_command = 'definition {0} {1} {2}\n'.format( str(line+1), str(col+1), filename.replace('\\','/') )
		AsyncCommand(definition_command, \
			lambda async_command: callback(json.loads(async_command.result), **async_command.payload ),
			_id="definition_command" \
			).add_payload(filename=filename, line=line, col=col) \
			.append_to_global_queue(filename)


	# REFERENCES
	def references(self, filename, line, col, callback):
		references_command = 'references {0} {1} {2}\n'.format( str(line+1), str(col+1), filename.replace('\\','/') )
		AsyncCommand(references_command, \
			lambda async_command: callback(json.loads(async_command.result), **async_command.payload ),
			_id="references_command" \
			).add_payload(filename=filename, line=line, col=col) \
			.append_to_global_queue(filename)


	# STRUCTURE
	def structure(self, filename, callback):
		structure_command = 'structure {0}\n'.format(filename.replace('\\','/'))
		AsyncCommand(structure_command, \
			lambda async_command: callback(json.loads(async_command.result), **async_command.payload ),
			_id="structure_command" \
			).add_payload(filename=filename) \
			.append_to_global_queue(filename)



	# ASK FOR COMPLETIONS
	def complete(self, filename, line, col, member, callback):
		completions_command = 'completions {0} {1} {2} {3}\n'.format(member, str(line+1), str(col+1), filename.replace('\\','/'))
		AsyncCommand(completions_command,
			lambda async_command: callback( async_command.result, **async_command.payload ),
			_id="completions_command" \
			).add_payload() \
			.append_to_global_queue(filename)


	# UPDATE FILE
	def update(self, filename, lines, content):
		update_cmdline = 'update nocheck {0} {1}\n{2}\n'.format(str(lines+1),filename.replace('\\','/'),content)
		AsyncCommand(update_cmdline, None, 'update %s' % filename).append_to_global_queue(filename)
		# Always update because it's almost no overhead, but remember if anything has changed
		if self.need_update(filename, content):
			self.on_file_contents_have_changed()
			

	# ADD FILE
	def add(self, root, filename, lines, content):
		update_cmdline = 'update nocheck {0} {1}\n{2}\n'.format(str(lines+1),filename.replace('\\','/'),content)
		AsyncCommand(update_cmdline, None, 'add %s' % filename).append_to_global_queue(root) ## root here makes the difference to update
		# Always update because it's almost no overhead, but remember if anything has changed
		self.on_file_contents_have_changed()
	

	def on_file_contents_have_changed(self):
		self.executed_with_most_recent_file_contents = []

	def need_update(self, filename, unsaved_content):
		newhash = self.make_hash(filename, unsaved_content)
		oldhash = self.added_files[filename] if filename in self.added_files else "wre"
		if newhash == oldhash:
			print("NO UPDATE needed for file : %s" % filename)
			return False
		else:
			print("UPDATE needed for file %s : %s" % (newhash, filename) )
			self.added_files[filename] = newhash
			return True

	def make_hash(self, filename, unsaved_content):
		return hashlib.md5(encode(unsaved_content)).hexdigest()

	# ERRORS
	# callback format: def x(result, filename)
	def set_default_errors_callback(self, callback):
		self.default_errors_callback = callback
		
	def errors(self, filename, callback=None):
		if not callback:
			callback = self.default_errors_callback
		# only update if something in the files has changed since last execution
		if 'errors' in self.executed_with_most_recent_file_contents:
			return
		self.executed_with_most_recent_file_contents.append('errors')
		AsyncCommand('showErrors\n', \
			lambda async_command: callback(async_command.result, async_command.payload['filename'] ),
			_id="showErrors" \
			).add_payload(filename=filename) \
			.procrastinate() \
			.append_to_global_queue(filename)	
			

	# KILL PROCESS
	def kill(self,filename):
		process = self.get_process(filename)
		if process == None:
			return


		def async_react_files(files):
			if not files: # TODO: why?
				return
				
			# don't quit tss if an added *.ts file is still open in an editor view
			views = sublime.active_window().views()
			for v in views:
				if v.file_name() == None:
					continue
				for f in files:
					if v.file_name().replace('\\','/').lower() == f.lower() and not is_dts(v):
						return

			def killAndRemove():
				process.kill()
				PROCESSES.remove(LISTE.get_root(filename))
				MESSAGE.show('TypeScript project close',True)
				self.notify('kill', process)

			# send quit and kill process afterwards
			AsyncCommand('quit\n', killAndRemove, 'quit').append_to_global_queue(filename)	
			# if the tss process has hang up (previous lambda will not be executed)
			# , force kill after 5 sek
			sublime.set_timeout(killAndRemove,5000)
			

		sublime.active_window().run_command('save_all')
		self.files(filename, async_react_files)
		

		
		
		
	listeners = {}
	# LIST OF EVENT TYPES:
	# kill

	# NOTIFY LISTENERS
	def notify(self, event_type, process):
		if process.root not in self.listeners: return
		for f in self.listeners[process.root][event_type]:
			f(process)


	# ADD EVENT LISTENER
	def addEventListener(self, event_type, root, callback):
		if root not in self.listeners:
			self.listeners[root] = {}
		if type not in self.listeners[root]:
			self.listeners[root][event_type] = []
		self.listeners[root][event_type].append(callback)


	# REMOVE EVENT LISTENER
	def removeEventListener(self, event_type, root, callback):
		if root not in self.listeners: return
		if type not in self.listeners[root]: return

		to_delete = []
		for f in self.listeners[root][event_type]:
			if f == callback:
				to_delete.append(f)

		for f in to_delete:
			self.listeners[root][event_type].remove(f)


# --------------------------------------- INITIALISATION -------------------------------------- #

TSS = Tss()
