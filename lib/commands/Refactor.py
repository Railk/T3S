from subprocess import Popen, PIPE
from threading import Thread
try:
	from queue import Queue
except ImportError:
	from Queue import Queue

import sublime
import os
import json

from ..Tss import TSS
from ..display.Panel import PANEL
from ..system.Settings import SETTINGS
from ..Utils import debounce, dirname, get_data, get_kwargs, ST3


# ----------------------------------------- UTILS --------------------------------------- #

def show_output(window,line):
	PANEL.show(window)
	PANEL.update(line['output'])

def clear_panel(window):
	PANEL.clear(window)


# --------------------------------------- COMPILER -------------------------------------- #

class Refactor(Thread):

	def __init__(self, window, member, refs):
		self.window = window
		self.member = member
		self.refs = refs
		Thread.__init__(self)

	def run(self):
		if ST3:clear_panel(self.window)
		else: sublime.set_timeout(lambda:clear_panel(self.window),0)

		node = SETTINGS.get_node()
		kwargs = get_kwargs()
		p = Popen([node, os.path.join(dirname,'bin','refactor.js'), self.member, json.dumps(self.refs)], stdin=PIPE, stdout=PIPE, **kwargs)	 
		reader = RefactorReader(self.window,p.stdout,Queue())
		reader.daemon = True
		reader.start()


class RefactorReader(Thread):

	def __init__(self,window,stdout,queue):
		self.window = window
		self.stdout = stdout
		self.queue = queue
		Thread.__init__(self)

	def run(self):
		delay = 1000
		previous = ""
		for line in iter(self.stdout.readline, b''):
			line = json.loads(line.decode('UTF-8'))
			if 'output' in line:
				if ST3: show_output(self.window,line)
				else: sublime.set_timeout(lambda:show_output(self.window,line),0)
			elif 'file' in line:
				filename = line['file']
				content = get_data(filename)
				lines = len(content.split('\n'))-1
				if previous != filename:
					self.send(filename,lines,content,delay)
					delay+=100

				previous = filename
			else:
				print('refactor error')

		
		self.stdout.close()

	def send(self,filename,lines,content,delay):
		sublime.set_timeout(lambda:self.update(filename,lines,content),delay)

	def update(self,filename,lines,content):
		TSS.update(filename,lines,content)
		TSS.errors(filename)
		
		
		
