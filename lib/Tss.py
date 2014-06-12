# coding=utf8

import sublime
import json

from .display.Completion import COMPLETION
from .display.Message import MESSAGE
from .system.Processes import PROCESSES, AsyncCommand
from .system.Liste import LISTE
from .Utils import is_dts


# --------------------------------------- TSS -------------------------------------- #

class Tss(object):




	# GET PROCESS
	def get_process(self,filename):
		return PROCESSES.get(LISTE.get_root(filename))


	# INIT ROOT FILE
	def init(self,root):
		PROCESSES.add(root, self.notify)


	# RELOAD PROCESS
	def reload(self,filename):
		AsyncCommand('reload\n', None, 'reload').append_to_global_queue(filename)
		self.errors(filename)	

	# GET INDEXED FILES
	def files(self,filename):
		return "TODO: implement async files"
		process = self.get_process(filename)
		if process == None:
			return
		
		return json.loads(process.send('files\n'))


	# DUMP FILE
	def dump(self,filename,output):
		return "TODO: implement async dump"
		process = self.get_process(filename)
		if process == None:
			return

		print(process.send('dump {0} {1}\n'.format(output,filename.replace('\\','/'))))


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
	def structure(self,filename):
		return  []
		process = self.get_process(filename)
		if process == None:
			return

		return json.loads(process.send('structure {0}\n'.format(filename.replace('\\','/'))))


	# ASK FOR COMPLETIONS
	def complete(self,filename,line,col,member):
		return  COMPLETION.prepare_list('{ entries: [{name: "TODO: implement async Completions", type: "todo", docComment: "todo"}]   }')
		
		process = self.get_process(filename)
		if process == None:
			return

		COMPLETION.prepare_list(process.send('completions {0} {1} {2} {3}\n'.format(member,str(line+1),str(col+1),filename.replace('\\','/'))))


	# UPDATE FILE
	def update(self,filename,lines,content):
		update_cmdline = 'update nocheck {0} {1}\n{2}\n'.format(str(lines+1),filename.replace('\\','/'),content)
		AsyncCommand(update_cmdline, None, 'update %s' % filename).append_to_global_queue(filename)
		return
		
		process = self.get_process(filename)
		if process == None:
			return

		process.send_async(update)
		process.send(update)
			

	# ADD FILE
	def add(self,root,filename,lines,content):
		update_cmdline = 'update nocheck {0} {1}\n{2}\n'.format(str(lines+1),filename.replace('\\','/'),content)
		AsyncCommand(update_cmdline, None, 'add %s' % filename).append_to_global_queue(root) ## root here makes the difference to update
		
		return
		process = self.get_process(root)
		if process == None:
			return

		process.send_async(update)
		process.send(update)


	# ERRORS
	# callback format: def x(result, filename)
	def set_default_errors_callback(self, callback):
		self.default_errors_callback = callback
		
	def errors(self, filename, callback=None):
		if not callback:
			callback = self.default_errors_callback
			
		AsyncCommand('showErrors\n', \
			lambda async_command: callback(async_command.result, async_command.payload['filename'] ),
			_id="showErrors" \
			).add_payload(filename=filename) \
			.procrastinate() \
			.append_to_global_queue(filename)	
			
		return
		
		process = self.get_process(filename)
		if process == None:
			return

		process.send_async('showErrors\n')
	

	# KILL PROCESS
	def kill(self,filename):
		process = self.get_process(filename)
		if process == None:
			return

		sublime.active_window().run_command('save_all')
		files = self.files(filename)
		# TODO: why?
		if not files:
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
