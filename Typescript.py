# coding=utf8

import sublime
import sublime_plugin
from Queue import Queue
from threading import Thread
from subprocess import Popen, PIPE
import subprocess
import os
import json
import re
import sys


# --------------------------------------- CONSTANT -------------------------------------- #
if os.name == 'nt':
	ICONS_PATH = ".."+os.path.join(os.path.dirname(os.path.realpath(__file__)).split('Packages')[1], 'icons', 'bright-illegal')
else:
	ICONS_PATH = "Packages"+os.path.join(os.path.dirname(os.path.realpath(__file__)).split('Packages')[1], 'icons', 'bright-illegal.png')


ICONS_PATH = os.path.join('..', 'Typescript', 'icons')
TSS_PATH =  os.path.join(os.path.dirname(os.path.realpath(__file__)),'bin','tss.js')
GLOBALS = {}
ERRORS = {}
COMPLETION_LIST = []
ERRORS_LIST = []


# -------------------------------------- UTILITIES -------------------------------------- #

def get_lines(view):
	(line,col) = view.rowcol(view.size())
	return line

def get_content(view):
	return view.substr(sublime.Region(0, view.size()))

js_id_re = re.compile(u'^[_$a-zA-Z\u00FF-\uFFFF][_$a-zA-Z0-9\u00FF-\uFFFF]*')
def is_member_completion(line):
	def partial_completion():
		sp = line.split(".")
		if len(sp) > 1:
			return js_id_re.match(sp[-1]) is not None
		return False
	return line.endswith(".") or partial_completion()


# ----------------------------------------- TSS ----------------------------------------- #

class Tss(object):

	queues = {}
	processes = {}
	threads = []
	errors_list = []
	prefixes = {
		'method': u'◉',
		'property': u'●',
		'class':u'◆',
		'interface':u'◇',
		'keyword':u'∆',
		'variable': u'∨',
		'public':u'[pub]',
		'private':u'[priv]'
	}

	data = {
		'string':u'"string"',
		'boolean':u'false',
		'Object':u'{"key":"value"}',
		'{}':u'{"key":"value"}',
		'any':'"any"',
		'any[]':'"[]"',
		'HTMLElement':'"HTMLElement"',
		'Function':'function(){}',
		'number':'0.0'
	}


	# GET PROCESS
	def get_process(self,view):
		filename = view.file_name()
		if filename in self.processes:
			return self.processes[filename]

		return None


	# START PROCESS
	def start(self,view,filename,added):
		if filename in self.processes:
			if added != None: 
				self.processes[added] = self.processes[filename]
				self.queues[added] = self.queues[filename]
				self.update(view,get_content(view),get_lines(view))
			return

		self.queues[filename] = {'stdin':Queue(),'stdout':Queue()}
		if added != None: self.queues[added] = self.queues[filename]

		thread = TssInit(filename,self.queues[filename]['stdin'],self.queues[filename]['stdout'])
		self.add_thread(thread)
		self.handle_threads(filename,added)


	# RELOAD PROCESS
	def reload(self,view):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(bytes('reload\n'))
		process.stdout.readline().decode('UTF-8')


	# KILL PROCESS
	def kill(self,view):
		process = self.get_process(view)
		if process == None:
			return

		del self.processes[view.file_name()]


	# ASK FOR COMPLETIONS
	def complete(self,view,line,col,member):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(bytes('completions {0} {1} {2} {3}\n'.format(member,str(line+1),str(col+1),view.file_name().replace('\\','/'))))
		data = process.stdout.readline().decode('UTF-8')

		try:
			entries = json.loads(data)['entries']
		except:
			entries =[]

		self.prepare_completions_list(entries)
	

	# UPDATE FILE
	def update(self,view,content,lines):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(bytes('update {0} {1}\n'.format(str(lines+1),view.file_name().replace('\\','/'))))
		process.stdin.write(bytes(content+'\n'))
		process.stdout.readline().decode('UTF-8')


	# GET ERRORS
	def errors(self,view,content,lines):
		if self.get_process(view) == None:
		 	return
		
		del ERRORS_LIST[:]
		filename = view.file_name()
		self.queues[filename]['stdin'].put(bytes('update {0} {1}\n'.format(str(lines+1),filename.replace('\\','/'))))
		self.queues[filename]['stdin'].put(bytes(content+'\n'))
		self.queues[filename]['stdin'].put(bytes('showErrors\n'.format(filename.replace('\\','/'))))


	# ADD THREADS
	def add_thread(self,thread):
		self.threads.append(thread)
		thread.daemon = True
		thread.start()

	
	#HANDLE THREADS
	def handle_threads(self,filename,added, i=0, dir=1):
		next_threads = []

		for thread in self.threads:
			if thread.is_alive():
				next_threads.append(thread)
				continue

			self.processes[filename] = thread.result
			if added != None: self.processes[added] = self.processes[filename]
		
		self.threads = next_threads

		if len(self.threads):
			before = i % 8
			after = (7) - before
			if not after:
				dir = -1
			if not before:
				dir = 1
			i += dir
			sublime.status_message(' Typescript is initializing [%s=%s]' % \
				(' ' * before, ' ' * after))

			sublime.set_timeout(lambda: self.handle_threads(filename,added,i,dir), 100)
			return

		sublime.status_message('')
		
		view = sublime.active_window().active_view()
		self.errors(view,get_content(view),get_lines(view))


	# COMPLETIONS LIST
	def prepare_completions_list(self,entries):
		del COMPLETION_LIST[:]
		
		for entry in entries:
			key = self.get_completions_list_key(entry)
			value = self.get_completions_list_value(entry)
			COMPLETION_LIST.append((key,value))

		COMPLETION_LIST.sort()


	def get_completions_list_key(self,entry):
		kindModifiers = self.prefixes[entry['kindModifiers']] if entry['kindModifiers'] in self.prefixes else ""
		kind = self.prefixes[entry['kind']] if entry['kind'] in self.prefixes else ""

		return kindModifiers+' '+kind+' '+str(entry['name'])+' '+str(entry['type'])


	def get_completions_list_value(self,entry):
		match = re.match('\(([a-zA-Z :,?\{\}\[\]]*)\):',str(entry['type']))
		result = []

		if match:
			variables = match.group(1).split(',')
			for variable in variables:
				splits = variable.split(':')
				if len(splits) > 1:
					split = splits[1].replace(' ','')
					data = self.data[split] if split in self.data else "" 
					result.append(data)
				else:
					result.append('')

			return entry['name']+'('+','.join(result)+');'
		else:
			return entry['name']

	# ERRORS
	def highlight_errors(self,view,errors) :
		try:
			errors = json.loads(errors)
			for e in errors :
				ERRORS_LIST.append(e)
		except:
			pass

		filename = view.file_name()
		char_regions = []

		ERRORS[filename] = {}
		for e in ERRORS_LIST :
			if os.path.realpath(e['file']) == filename:
				start_line = e['start']['line']
				end_line = e['end']['line']
				left = e['start']['character']
				right = e['end']['character']

				a = view.text_point(start_line-1,left-1)
				b = view.text_point(end_line-1,right-1)
				char_regions.append( sublime.Region(a,b))
				ERRORS[filename][(a,b)] = e['text']

		view.add_regions('typescript-error' , char_regions , 'invalid' , ICONS_PATH)


	def set_error_status(self,view):
		error = self.get_error_at(view.sel()[0].begin(),view.file_name())
		if error != None:
			sublime.status_message(error)
		else:
			sublime.status_message('')


	def get_error_at(self,pos,filename):
		if filename in ERRORS:
			for (l, h), error in ERRORS[filename].iteritems():
				if pos >= l and pos <= h:
					return error

		return None



# ----------------------------------------- TSS THREADs ---------------------------------------- #

class TssInit(Thread):

	def __init__(self, filename, stdin_queue, stdout_queue):
		self.filename = filename
		self.stdin_queue = stdin_queue
		self.stdout_queue = stdout_queue
		self.result = ""
		Thread.__init__(self)

	def run(self):
		kwargs = {}
		cmd = 'tss'
		if os.name == 'nt':
			errorlog = open(os.devnull, 'w')
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			kwargs = {'stderr':errorlog, 'startupinfo':startupinfo}
			cmd = 'tss.cmd'

		if sys.platform == "darwin":
			self.result = Popen(['/usr/local/bin/node', '/usr/local/lib/node_modules/tss/bin/tss.js' ,self.filename], stdin=PIPE, stdout=PIPE, **kwargs)
			p = Popen(['/usr/local/bin/node', '/usr/local/lib/node_modules/tss/bin/tss.js', self.filename], stdin=PIPE, stdout=PIPE, **kwargs)
		else:
			self.result = Popen([cmd, self.filename], stdin=PIPE, stdout=PIPE, **kwargs)
			p = Popen([cmd, self.filename], stdin=PIPE, stdout=PIPE, **kwargs)
		
		self.result.stdout.readline().decode('UTF-8')
		p.stdout.readline().decode('UTF-8')
		
		tssWriter = TssWriter(p.stdin,self.stdin_queue)
		tssWriter.daemon = True
		tssWriter.start()

		tssReader = TssReader(p.stdout,self.stdout_queue)
		tssReader.daemon = True
		tssReader.start()


class TssWriter(Thread):

	def __init__(self,stdin,queue):
		self.stdin = stdin
		self.queue = queue
		Thread.__init__(self)

	def run(self):
		for item in iter(self.queue.get, None):
			self.stdin.write(item)
		self.stdin.close()


class TssReader(Thread):

	def __init__(self,stdout,queue):
		self.stdout = stdout
		self.queue = queue
		Thread.__init__(self)

	def run(self):
		for line in iter(self.stdout.readline, b''):
			if line.startswith('"updated'):
				continue
			else:
				sublime.set_timeout(lambda: GLOBALS['tss'].highlight_errors(sublime.active_window().active_view(),line), 1)

		self.stdout.close()


# --------------------------------------- EVENT LISTENERS -------------------------------------- #

class TypescriptComplete(sublime_plugin.TextCommand):

	def run(self, edit, characters):
		for region in self.view.sel():
			self.view.insert(edit, region.end(), characters)

		tss = GLOBALS['tss']
		tss.update(self.view,get_content(self.view),get_lines(self.view))

		self.view.run_command('auto_complete',{
			'disable_auto_insert': True,
			'api_completions_only': True,
			'next_competion_if_showing': True
		})
		


class TypescriptEventListener(sublime_plugin.EventListener):

	pending = 0

	def __init__(self):
		GLOBALS['tss'] = self.tss = Tss()
		self.settings = sublime.load_settings('Typescript.sublime-settings')


	def on_activated(self,view):
		if not self.is_ts(view):
			return

		self.start(view)


	def on_clone(self,view):
		if not self.is_ts(view):
			return

		self.start(view)


	def start(self,view):
		view.settings().set('auto_complete',False)
		view.settings().set('extensions',['ts'])
		filename = view.file_name()
		root = self.get_root()
		added = None
		if root != None:
			added = filename
			filename = root

		self.tss.start(view,filename,added)


	# def on_close(self,view):
	# 	if not self.is_ts(view):
	# 		return

	# 	self.tss.kill(view)


	def on_post_save(self,view):
		if not self.is_ts(view):
			return

		content = get_content(view)
		lines = get_lines(view)
		self.tss.update(view,content,lines)
		self.tss.errors(view,content,lines)


	def on_selection_modified(self, view):
		if not self.is_ts(view):
			return

		self.tss.set_error_status(view)
		

	def on_modified(self,view):
		if view.is_loading(): return
		if not self.is_ts(view):
			return

		# content = get_content(view)
		# lines = get_lines(view)
		# self.tss.update(view,content,lines)
		self.pending = self.pending + 1
		sublime.set_timeout(lambda:self.handle_timeout(view),180)


	def handle_timeout(self,view):
		self.pending = self.pending -1
		if self.pending == 0:
			content = get_content(view)
			lines = get_lines(view)
			self.tss.errors(view,content,lines)


	def on_query_completions(self, view, prefix, locations):
		if self.is_ts(view):
			pos = view.sel()[0].begin()
			(line, col) = view.rowcol(pos)
			is_member = str(is_member_completion(view.substr(sublime.Region(view.line(pos-1).a, pos)))).lower()
			self.tss.complete(view,line,col,is_member)

			return COMPLETION_LIST


	def on_query_context(self, view, key, operator, operand, match_all):
		if key == "typescript":
			view = sublime.active_window().active_view()
			return self.is_ts(view)


	def is_ts(self,view):
		return view.file_name() and view.file_name().endswith('.ts')


	def get_root(self):
		project_settings = sublime.active_window().active_view().settings().get('typescript')
		current_folder = os.path.dirname(os.path.realpath(sublime.active_window().active_view().file_name()))

		if(project_settings != None):
			for root in project_settings:
				root_folder = os.path.dirname(os.path.realpath(root))
				if root_folder == current_folder:
					return root

			return None
		else:
			top_folder = None
			open_folders = sublime.active_window().folders()
			for folder in open_folders:
				folder = os.path.realpath(folder)
				if current_folder.startswith(folder):
					top_folder = folder
					break

			segments = current_folder.replace('\\','/').split('/')
			length = len(segments)
			segment_range =reversed(range(0,length+1))

			for index in segment_range:
				folder = self.join_segments(segments,index)
				config_file = os.path.join(folder,'.sublimets')
				config_data = self.get_data(config_file)
				if config_data != None:
					return os.path.join(folder,config_data['root'])

				if folder == top_folder:
					break

			return None


	def get_data(self,file):
		if os.path.isfile(file): 
			try: 
				f = open(file,'r').read()
				return json.loads(f)
			except IOError: 
				pass

		return None


	def join_segments(self,liste,length):
		join = ""
		for index in reversed(range(0,length)):
			join = liste[index] +'/'+ join 

		return os.path.realpath(join)