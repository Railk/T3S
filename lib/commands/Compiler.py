from subprocess import Popen, PIPE
from threading import Thread
try:
	from queue import Queue
except ImportError:
	from Queue import Queue

import sublime
import os
import json

from ..Utils import dirname, get_kwargs, ST3, Debug
from ..display.Panel import PANEL
from ..system.Settings import SETTINGS

# ----------------------------------------- UTILS --------------------------------------- #

def show_output(window,line):
	PANEL.show(window)
	PANEL.update(line['output'].replace('[end]','\n'))
	window.run_command('typescript_build_view',{"filename":line['output'].replace('[end]','\n')})

def show_view(window,line):
	window.run_command('typescript_build_view',{"filename":line['filename'].replace('\n','')})

def clear_panel(window):
	PANEL.clear(window)


# --------------------------------------- COMPILER -------------------------------------- #

class Compiler(Thread):

	def __init__(self, window, root, filename):
		self.window = window
		self.root = root
		self.filename = filename
		Thread.__init__(self)

	def run(self):
		Debug('build', 'BUILD INITIALIZED')
		node = SETTINGS.get_node(self.root)
		kwargs = get_kwargs()
		settings = json.dumps(SETTINGS.get('build_parameters', self.root))

		if ST3:
			clear_panel(self.window)
		else:
			sublime.set_timeout(lambda: clear_panel(self.window),0)


		cmd = [node, os.path.join(dirname,'bin','build.js'), settings, self.root, self.filename]
		Debug('build', 'EXECUTE: %s' % str(cmd))
		p = Popen(cmd, stdin=PIPE, stdout=PIPE, **kwargs)


		reader = CompilerReader(self.window,p.stdout,Queue())
		reader.daemon = True
		reader.start()


class CompilerReader(Thread):

	def __init__(self,window,stdout,queue):
		self.window = window
		self.stdout = stdout
		self.queue = queue
		Thread.__init__(self)

	def run(self):
		Debug('build+', 'BUILD RESULTS READER THREAD started')
		for line in iter(self.stdout.readline, b''):
			Debug('build+', 'BUILD RESULTS: %s' % line)
			try:
				line = json.loads(line.decode('UTF-8'))
			except ValueError as v:
				print('T3S ERROR: NON JSON ANSWER from build.js: %s' % line.decode('UTF-8'))
				print('T3S: compiler error')
				break
			if 'output' in line:
				if ST3:
					show_output(self.window,line)
				else:
					sublime.set_timeout(lambda:show_output(self.window,line),0)
			elif 'filename' in line:
				if ST3:
					show_view(self.window,line)
				else:
					sublime.set_timeout(lambda:show_view(self.window,line),0)
			else:
				print('T3S: compiler error')
		Debug('build+', 'BUILD RESULTS READER THREAD finished')
		self.stdout.close()

