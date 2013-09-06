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

# do not use realpath because it breaks on symlinked packages
dirname = os.path.dirname(__file__)

if os.name == 'nt':
	ICONS_PATH = ".."+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-illegal')
else:
	ICONS_PATH = "Packages"+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-illegal.png')

TSS_PATH =  os.path.join(os.path.dirname(__file__),'bin','tss.js')
ERRORS = {}
COMPLETION_LIST = []
ERRORS_LIST = []


# -------------------------------------- UTILITIES -------------------------------------- #

def is_ts(view):
	return view.file_name() and view.file_name().endswith('.ts') 

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
		'method': u'○',
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
			if added != None and added not in self.processes:
				self.processes[added] = self.processes[filename]
				self.queues[added] = self.queues[filename]
				self.update(view,get_content(view),get_lines(view))
			return

		self.processes[filename] = None
		self.queues[filename] = {'stdin':Queue(),'stdout':Queue()}
		if added != None: self.queues[added] = self.queues[filename]

		settings = sublime.load_settings('Typescript.sublime-settings')
		thread = TssInit(filename,self.queues[filename]['stdin'],self.queues[filename]['stdout'],settings.get('local_tss'))
		self.add_thread(thread)
		self.handle_threads(filename,added)


	# RELOAD PROCESS
	def reload(self,view):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(self.encode('reload\n'))
		process.stdout.readline().decode('UTF-8')


	# KILL PROCESS
	def kill(self,view):
		process = self.get_process(view)
		if process == None:
			return

		del self.processes[view.file_name()]


	# DUMP FILE
	def dump(self,view,output):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(self.encode('dump {0} {1}\n'.format(output,view.file_name().replace('\\','/')),'UTF-8'))
		print(process.stdout.readline().decode('UTF-8'))


	# ASK FOR COMPLETIONS
	def complete(self,view,line,col,member):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(self.encode('completions {0} {1} {2} {3}\n'.format(member,str(line+1),str(col+1),view.file_name().replace('\\','/'))))
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

		process.stdin.write(self.encode('update nocheck {0} {1}\n'.format(str(lines+1),view.file_name().replace('\\','/'))))
		process.stdin.write(self.encode(content+'\n'))
		process.stdout.readline().decode('UTF-8')


	# GET ERRORS
	def errors(self,view,content,lines):
		if self.get_process(view) == None:
		 	return
		
		del ERRORS_LIST[:]
		filename = view.file_name()
		self.queues[filename]['stdin'].put(self.encode('update nocheck {0} {1}\n'.format(str(lines+1),filename.replace('\\','/'))))
		self.queues[filename]['stdin'].put(self.encode(content+'\n'))
		self.queues[filename]['stdin'].put(self.encode('showErrors\n'.format(filename.replace('\\','/'))))

	
	def get_panel_errors(self,view):
		process = self.get_process(view)
		if process == None:
			return

		filename = view.file_name()
		(lineCount, col) = view.rowcol(view.size())
		content = view.substr(sublime.Region(0, view.size()))
		process.stdin.write(self.encode('update nocheck {0} {1}\n'.format(str(lineCount+1),filename.replace('\\','/'))))
		process.stdin.write(self.encode(content+'\n'))
		process.stdout.readline().decode('UTF-8')
		process.stdin.write(self.encode('showErrors\n'.format(filename.replace('\\','/'))))
		return json.loads(process.stdout.readline().decode('UTF-8'))


	# ENCODE STRING
	def encode(self,content):
		return content.encode('UTF-8')


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
			count = 1
			for variable in variables:
				splits = variable.split(':')
				if len(splits) > 1:
					split = splits[1].replace(' ','')
					data = self.data[split] if split in self.data else ""
					data = '${'+str(count)+':'+data+'}'
					result.append(data)
					count = count+1
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
			if os.path.realpath(e['file']).lower() == filename.lower():
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

	def __init__(self, filename, stdin_queue, stdout_queue, local):
		self.filename = filename
		self.stdin_queue = stdin_queue
		self.stdout_queue = stdout_queue
		self.result = ""
		self.local = local
		Thread.__init__(self)

	def run(self):
		kwargs = {}
		cmd='tss'
		if os.name == 'nt':
			errorlog = open(os.devnull, 'w')
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			kwargs = {'stderr':errorlog, 'startupinfo':startupinfo}
			cmd = 'tss.cmd'

		print('typescript initializing')


		if self.local:
			if sys.platform == "darwin":
				self.result = Popen(['/usr/local/bin/node', TSS_PATH ,self.filename], stdin=PIPE, stdout=PIPE, **kwargs)
				p = Popen(['/usr/local/bin/node', TSS_PATH, self.filename], stdin=PIPE, stdout=PIPE, **kwargs)
			else:
				self.result = Popen(['node', TSS_PATH, self.filename], stdin=PIPE, stdout=PIPE, **kwargs)
				p = Popen(['node', TSS_PATH, self.filename], stdin=PIPE, stdout=PIPE, **kwargs)
		else:
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
				sublime.set_timeout(lambda: TSS.highlight_errors(sublime.active_window().active_view(),line), 1)

		self.stdout.close()


# --------------------------------------- EVENT LISTENERS -------------------------------------- #

class TypescriptErrorPanel(sublime_plugin.TextCommand):

	def run(self, edit, characters):
		self.files = []
		self.regions = []
		liste = []
		errors = TSS.get_panel_errors(self.view)
		
		try:
			for e in errors:
				segments = e['file'].split('/')
				last = len(segments)-1
				filename = segments[last]
				view = sublime.active_window().open_file(e['file'], sublime.TRANSIENT)

				start_line = e['start']['line']
				end_line = e['end']['line']
				left = e['start']['character']
				right = e['end']['character']

				a = self.view.text_point(start_line-1,left-1)
				b = self.view.text_point(end_line-1,right-1)

				file_info = filename + " Line " + str(start_line) + " - "
				title = self.error_text(e)
				description = file_info + view.substr(view.full_line(a)).strip()

				liste.append([title, description])
				self.regions.append( sublime.Region(a,b))
				self.files.append(e['file'])

			if len(liste) == 0: liste.append('no errors')

			sublime.active_window().show_quick_panel(liste,self.on_done)
		except (Exception) as e:
			sublime.message_dialog("error panel : plugin not yet intialize please retry after initialisation")

		
	def on_done(self,index):
		if index == -1: return
		
		view = sublime.active_window().open_file(self.files[index])
		view.show(self.regions[index])
		sublime.active_window().focus_view(view)

	def error_text(self,error):
		text = error['text']
		text = re.sub(r'^.*?:\s*', '', text)
		return text



class TypescriptComplete(sublime_plugin.TextCommand):

	def run(self, edit, characters):
		for region in self.view.sel():
			self.view.insert(edit, region.end(), characters)

		TSS.update(self.view,get_content(self.view),get_lines(self.view))

		self.view.run_command('auto_complete',{
			'disable_auto_insert': True,
			'api_completions_only': True,
			'next_competion_if_showing': True
		})
		


class TypescriptEventListener(sublime_plugin.EventListener):

	pending = 0
	settings = None

	def on_activated(self,view):
		self.init_view(view)


	def on_clone(self,view):
		self.init_view(view)


	def init_view(self,view):
		self.settings = sublime.load_settings('Typescript.sublime-settings')
		init(view)
		content = get_content(view)
		lines = get_lines(view)
		TSS.errors(view,content,lines)


	# def on_close(self,view):
	# 	if not is_ts(view):
	# 		return

	# 	TSS.kill(view)


	def on_post_save(self,view):
		if not is_ts(view):
			return

		content = get_content(view)
		lines = get_lines(view)
		TSS.update(view,content,lines)
		TSS.errors(view,content,lines)


	def on_selection_modified(self, view):
		if not is_ts(view):
			return

		TSS.set_error_status(view)
		

	def on_modified(self,view):
		if view.is_loading(): return
		if not is_ts(view):
			return

		# content = get_content(view)
		# lines = get_lines(view)
		# TSS.update(view,content,lines)
		self.pending = self.pending + 1

		if self.settings == None:
			self.settings = sublime.load_settings('Typescript.sublime-settings')

		if not self.settings.get('error_on_save_only'):
			sublime.set_timeout(lambda:self.handle_timeout(view),180)


	def handle_timeout(self,view):
		self.pending = self.pending -1
		if self.pending == 0:
			content = get_content(view)
			lines = get_lines(view)
			TSS.errors(view,content,lines)


	def on_query_completions(self, view, prefix, locations):
		if is_ts(view):
			pos = view.sel()[0].begin()
			(line, col) = view.rowcol(pos)
			is_member = str(is_member_completion(view.substr(sublime.Region(view.line(pos-1).a, pos)))).lower()
			TSS.complete(view,line,col,is_member)

			return COMPLETION_LIST


	def on_query_context(self, view, key, operator, operand, match_all):
		if key == "typescript":
			view = sublime.active_window().active_view()
			return is_ts(view)




# ---------------------------------------- INITIALISATION --------------------------------------- #

TSS = Tss()

def init(view):
	if not is_ts(view): return

	filename = view.file_name()
	view.settings().set('auto_complete',False)
	view.settings().set('extensions',['ts'])
	
	root = get_root()
	added = None
	if root != None:
		if root != filename: added = filename
		filename = root

	TSS.start(view,filename,added)


def get_root():
	project_settings = sublime.active_window().active_view().settings().get('typescript')
	current_folder = os.path.dirname(os.path.realpath(sublime.active_window().active_view().file_name()))


	if(project_settings != None):
		for root in project_settings:
			root_folder = os.path.dirname(os.path.realpath(root))
			if root_folder.lower() == current_folder.lower():
				return root

		return None
	else:
		top_folder = None
		open_folders = sublime.active_window().folders()
		for folder in open_folders:
			folder = os.path.realpath(folder)
			if current_folder.lower().startswith(folder.lower()):
				top_folder = folder
				break

		segments = current_folder.replace('\\','/').split('/')
		segments[0] = top_folder.replace('\\','/').split('/')[0]
		length = len(segments)
		segment_range =reversed(range(0,length+1))

		for index in segment_range:
			folder = join_segments(segments,index)
			config_file = os.path.join(folder,'.sublimets')
			config_data = get_data(config_file)
			if config_data != None:
				return os.path.join(folder,config_data['root'])

			if folder.lower() == top_folder.lower():
				break

		return None


def get_data(file):
	if os.path.isfile(file): 
		try: 
			f = open(file,'r').read()
			return json.loads(f)
		except IOError: 
			pass

	return None


def join_segments(liste,length):
	join = ""
	for index in reversed(range(0,length)):
		join = liste[index] +'/'+ join 

	return os.path.realpath(join)



# ---------------------------------------- PLUGIN LOADED --------------------------------------- #

sublime.set_timeout(lambda:init(sublime.active_window().active_view()),500)
