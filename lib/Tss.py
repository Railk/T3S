# coding=utf8

import sublime
import json

from .display.Completion import COMPLETION
from .display.Message import MESSAGE
from .system.Processes import PROCESSES
from .system.Liste import LISTE
from .Utils import is_dts


# --------------------------------------- TSS -------------------------------------- #

class Tss(object):

	listeners = {}


	# GET PROCESS
	def get_process(self,filename):
		return PROCESSES.get(LISTE.get_root(filename))


	# INIT ROOT FILE
	def init(self,root):
		PROCESSES.add(root,self.notify)


	# RELOAD PROCESS
	def reload(self,filename,silent=False):
		process = self.get_process(filename)
		if process == None:
			return

		process.send_async('reload\n')
		process.send_async('showErrors\n')
		process.send('reload\n')
		process.send('showErrors\n')
		if not silent: MESSAGE.show('Project reloaded',True)


	# GET INDEXED FILES
	def files(self,filename):
		process = self.get_process(filename)
		if process == None:
			return
		
		return json.loads(process.send('files\n'))


	# DUMP FILE
	def dump(self,filename,output):
		process = self.get_process(filename)
		if process == None:
			return

		print(process.send('dump {0} {1}\n'.format(output,filename.replace('\\','/'))))


	# TYPE
	def type(self,filename,line,col):
		process = self.get_process(filename)
		if process == None:
			return

		return json.loads(process.send('type {0} {1} {2}\n'.format(str(line+1),str(col+1),filename.replace('\\','/'))))


	# DEFINITION
	def definition(self,filename,line,col):
		process = self.get_process(filename)
		if process == None:
			return

		return json.loads(process.send('definition {0} {1} {2}\n'.format(str(line+1),str(col+1),filename.replace('\\','/'))))


	# REFERENCES
	def references(self,filename,line,col):
		process = self.get_process(filename)
		if process == None:
			return

		return json.loads(process.send('references {0} {1} {2}\n'.format(str(line+1),str(col+1),filename.replace('\\','/'))))


	# STRUCTURE
	def structure(self,filename):
		process = self.get_process(filename)
		if process == None:
			return

		return json.loads(process.send('structure {0}\n'.format(filename.replace('\\','/'))))


	# ASK FOR COMPLETIONS
	def complete(self,filename,line,col,member):
		process = self.get_process(filename)
		if process == None:
			return

		COMPLETION.prepare_list(process.send('completions {0} {1} {2} {3}\n'.format(member,str(line+1),str(col+1),filename.replace('\\','/'))))


	# UPDATE FILE
	def update(self,filename,lines,content):
		process = self.get_process(filename)
		if process == None:
			return

		update = 'update nocheck {0} {1}\n{2}\n'.format(str(lines+1),filename.replace('\\','/'),content)
		process.send_async(update)
		process.send(update)
			

	# ADD FILE
	def add(self,root,filename,lines,content):
		process = self.get_process(root)
		if process == None:
			return

		update = 'update nocheck {0} {1}\n{2}\n'.format(str(lines+1),filename.replace('\\','/'),content)
		process.send_async(update)
		process.send(update)


	# ASYNC ERRORS
	def errors(self,filename):
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
		if not files: return

		views = sublime.active_window().views()
		for v in views:
			if v.file_name() == None: continue
			for f in files:
				if v.file_name().replace('\\','/').lower() == f.lower() and not is_dts(v):
					return

		process.send('quit\n')
		process.send_async('quit\n')
		process.kill()
		PROCESSES.remove(LISTE.get_root(filename))

		MESSAGE.show('TypeScript project close',True)
		self.notify('kill',process)


	# NOTIFY LISTENERS
	def notify(self,type,process):
		if process.root not in self.listeners: return
		for f in self.listeners[process.root][type]:
			f(process)


	# ADD LISTENER
	def addEventListener(self,type,root,function):
		if root not in self.listeners: self.listeners[root] = {}
		if type not in self.listeners[root]: self.listeners[root][type] = []
		self.listeners[root][type].append(function)


	# REMOVE LISTENER
	def removeEventListener(self,type,root,function):
		if root not in self.listeners: return
		if type not in self.listeners[root]: return

		to_delete = []
		for f in self.listeners[root][type]:
			if f == function:
				to_delete.append(f)

		for f in to_delete:
			self.listeners[root][type].remove(f)


# --------------------------------------- INITIALISATION -------------------------------------- #

TSS = Tss()