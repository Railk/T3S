# coding=utf8

import sublime
import sublime_plugin
from queue import Queue
from threading import Thread
from subprocess import Popen, PIPE
import subprocess
import os
import json
import re
import sys


# --------------------------------------- CONSTANT -------------------------------------- #

dirname = os.path.dirname(__file__)

if os.name == 'nt':
	ICONS_PATH = ".."+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-illegal')
else:
	ICONS_PATH = "Packages"+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-illegal.png')

TSS_PATH =  os.path.join(dirname,'bin','tss.js')
COMPLETION_LIST = []
ROOT_FILES = []
PROCESSES = []
ERRORS = {}


# -------------------------------------- UTILITIES -------------------------------------- #

def is_ts(view):
	return view.file_name() and view.file_name().endswith('.ts')

def is_dts(view):
	return view.file_name() and view.file_name().endswith('.d.ts')

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


# ----------------------------------------- TSS ---------------------------------------- #

class Tss(object):

	interface = False
	threads = []
	queues = {}
	processes = {}
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
		filename = view.file_name();
		if filename in self.processes:
			return self.processes[filename]

		return None


	# START PROCESS
	def start(self,view,filename,added):
		if filename in self.processes:
			if added != None and added not in self.processes:
				self.processes[added] = self.processes[filename]
				self.queues[added] = self.queues[filename]
				self.update(view)
			return

		self.processes[filename] = None
		self.queues[filename] = {'stdin':Queue(),'stdout':Queue()}
		if added != None: self.queues[added] = self.queues[filename]

		thread = TssInit(filename,self.queues[filename]['stdin'],self.queues[filename]['stdout'])
		self.add_thread(thread)
		self.handle_threads(view,filename,added)


	# RELOAD PROCESS
	def reload(self,view):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(bytes('reload\n','UTF-8'))
		print(process.stdout.readline().decode('UTF-8'))


	# GET INDEXED FILES
	def files(self,view):
		process = self.get_process(view)
		if process == None:
			return
		
		process.stdin.write(bytes('files\n','UTF-8'));
		print(process.stdout.readline().decode('UTF-8'))


	# KILL PROCESS
	def kill(self):

		del ROOT_FILES[:]
		del COMPLETION_LIST[:]
		self.threads= []
		ERRORS.clear()
		self.processes.clear()
		self.queues.clear()
		

		for process in PROCESSES:
			process.stdin.write(bytes('quit\n','UTF-8'))
			process.kill()

		del PROCESSES[:]

		sublime.status_message('typescript projects closed')


	# DUMP FILE
	def dump(self,view,output):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(bytes('dump {0} {1}\n'.format(output,view.file_name().replace('\\','/')),'UTF-8'))
		print(process.stdout.readline().decode('UTF-8'))


	# TYPE
	def type(self,view,line,col):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(bytes('type {0} {1} {2}\n'.format(str(line+1),str(col+1),view.file_name().replace('\\','/')),'UTF-8'))
		return json.loads(process.stdout.readline().decode('UTF-8'))


	# DEFINITION
	def definition(self,view,line,col):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(bytes('definition {0} {1} {2}\n'.format(str(line+1),str(col+1),view.file_name().replace('\\','/')),'UTF-8'))
		return json.loads(process.stdout.readline().decode('UTF-8'))


	# REFERENCES
	def references(self,view,line,col):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(bytes('references {0} {1} {2}\n'.format(str(line+1),str(col+1),view.file_name().replace('\\','/')),'UTF-8'))
		print(process.stdout.readline().decode('UTF-8'))

	# STRUCTURE
	def structure(self,view):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(bytes('structure {0}\n'.format(view.file_name().replace('\\','/')),'UTF-8'))
		return json.loads(process.stdout.readline().decode('UTF-8'))


	# ASK FOR COMPLETIONS
	def complete(self,view,line,col,member):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(bytes('completions {0} {1} {2} {3}\n'.format(member,str(line+1),str(col+1),view.file_name().replace('\\','/')),'UTF-8'))
		data = process.stdout.readline().decode('UTF-8')

		try:
			entries = json.loads(data)['entries']
		except:
			print('completion json error : ',data)
			entries = []
		
		self.prepare_completions_list(entries)


	# UPDATE FILE
	def update(self,view):
		process = self.get_process(view)
		if process == None:
			return

		(lineCount, col) = view.rowcol(view.size())
		content = view.substr(sublime.Region(0, view.size()))
		process.stdin.write(bytes('update nocheck {0} {1}\n'.format(str(lineCount+1),view.file_name().replace('\\','/')),'UTF-8'))
		process.stdin.write(bytes(content+'\n','UTF-8'))
		process.stdout.readline().decode('UTF-8')


	# GET ERRORS
	def errors(self,view):
		if self.get_process(view) == None:
			return

		filename = view.file_name()
		(lineCount, col) = view.rowcol(view.size())
		content = view.substr(sublime.Region(0, view.size()))
		self.queues[filename]['stdin'].put(bytes('update nocheck {0} {1}\n'.format(str(lineCount+1),filename.replace('\\','/')),'UTF-8'))
		self.queues[filename]['stdin'].put(bytes(content+'\n','UTF-8'))
		self.queues[filename]['stdin'].put(bytes('showErrors\n','UTF-8'))


	def get_panel_errors(self,view):
		process = self.get_process(view)
		if process == None:
			return

		filename = view.file_name()
		(lineCount, col) = view.rowcol(view.size())
		content = view.substr(sublime.Region(0, view.size()))
		process.stdin.write(bytes('update nocheck {0} {1}\n'.format(str(lineCount+1),filename.replace('\\','/')),'UTF-8'))
		process.stdin.write(bytes(content+'\n','UTF-8'))
		process.stdout.readline().decode('UTF-8')
		process.stdin.write(bytes('showErrors\n','UTF-8'))
		return json.loads(process.stdout.readline().decode('UTF-8'))


	# ADD THREADS
	def add_thread(self,thread):
		self.threads.append(thread)
		thread.daemon = True
		thread.start()

	
	#HANDLE THREADS
	def handle_threads(self,view,filename,added, i=0, dir=1):
		next_threads = []

		for thread in self.threads:
			if thread.is_alive():
				next_threads.append(thread)
				continue

			ROOT_FILES.append(view)
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

			sublime.set_timeout(lambda: self.handle_threads(view,filename,added,i,dir), 100)
			return

		sublime.status_message('')
		self.errors(sublime.active_window().active_view())


	# COMPLETIONS LIST
	def prepare_completions_list(self,entries):
		del COMPLETION_LIST[:]
		
		for entry in entries:
			if self.interface and entry['kind'] != 'interface': continue
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
	def show_errors(self,view,errors):
		try:
			errors = json.loads(errors)
			self.highlight_errors(view,errors)
		except:
			print('show_errors json error')


	def highlight_errors(self,view,errors) :
		char_regions = []
		filename = view.file_name()

		ERRORS[filename] = {}
		for e in errors :
			if e['file'].replace('/',os.sep).lower() == filename.lower():
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
			for (l, h), error in ERRORS[filename].items():
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
		self.settings = sublime.load_settings('Typescript.sublime-settings')
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

		print('typescript initializing')
		

		if self.settings.get('local_tss'):
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

		PROCESSES.append(self.result)
		PROCESSES.append(p)

		
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
			line = line.decode('UTF-8')
			if line.startswith('"updated') or line.startswith('"added'):
				continue
			else:
				TSS.show_errors(sublime.active_window().active_view(),line)

		self.stdout.close()



# --------------------------------------- COMMANDS -------------------------------------- #

# RELOAD PROJECT
class TypescriptReloadProject(sublime_plugin.TextCommand):

	def run(self, edit, characters=None):
		sublime.status_message('reloading project')
		TSS.reload(self.view)


# SHOW INFOS
class TypescriptType(sublime_plugin.TextCommand):

	prefixes = {
		'method': u'○',
		'property': u'●',
		'class':u'♦',
		'interface':u'◊',
		'keyword':u'∆',
		'constructor':u'■'
	}

	def run(self, edit, characters=None):
		pos = self.view.sel()[0].begin()
		(line, col) = self.view.rowcol(pos)
		types = TSS.type(self.view,line,col)

		if types == None: return
		if 'kind' not in types: return

		kind = self.prefixes[types['kind']] if types['kind'] in self.prefixes else ""
		if types['docComment'] != '':
			liste = types['docComment'].split('\n')+[kind+' '+types['fullSymbolName']+' '+types['type']]
		else :
			liste = [kind+' '+types['fullSymbolName']+' '+types['type']]

		self.view.show_popup_menu(liste,None)


# GO TO DEFINITION
class TypescriptDefinition(sublime_plugin.TextCommand):

	def run(self, edit, characters=None):
		pos = self.view.sel()[0].begin()
		(line, col) = self.view.rowcol(pos)
		definition = TSS.definition(self.view,line,col)

		if definition == None: return
		if 'file' not in definition: return

		view = sublime.active_window().open_file(definition['file'],sublime.TRANSIENT)
		self.open_view(view,definition)

	def open_view(self,view,definition):
		if view.is_loading():
			sublime.set_timeout(lambda: self.open_view(view,definition), 100)
			return
		else:
			start_line = definition['min']['line']
			end_line = definition['lim']['line']
			left = definition['min']['character']
			right = definition['lim']['character']

			a = view.text_point(start_line-1,left-1)
			b = view.text_point(end_line-1,right-1)
			region = sublime.Region(a,b)

			sublime.active_window().focus_view(view)
			view.show_at_center(region)
			view.add_regions('typescript-definition', [region], 'comment', 'dot', sublime.DRAW_NO_FILL)


class TypescriptReferences(sublime_plugin.TextCommand):

	def run(self, edit, characters=None):
		pos = self.view.sel()[0].begin()
		(line, col) = self.view.rowcol(pos)
		TSS.references(self.view,line,col)


# NAVIGATE IN FILE
class TypescriptStructure(sublime_plugin.TextCommand):

	prefixes = {
		'method': u'○',
		'property': u'●',
		'class':u'♦',
		'interface':u'◊',
		'keyword':u'∆',
		'constructor':u'■'
	}

	def run(self, edit, characters=None):
		self.regions = []
		liste = []
		members = TSS.structure(self.view)

		try:
			for member in members:
				start_line = member['min']['line']
				end_line = member['lim']['line']
				left = member['min']['character']
				right = member['lim']['character']

				a = self.view.text_point(start_line-1,left-1)
				b = self.view.text_point(end_line-1,right-1)
				self.regions.append(sublime.Region(a,b))

				kind = self.prefixes[member['loc']['kind']] if member['loc']['kind'] in self.prefixes else ""
				container_kind = self.prefixes[member['loc']['containerKind']] if member['loc']['containerKind'] in self.prefixes else ""
				liste.append([kind+' '+member['loc']['name']+' '+container_kind+' '+member['loc']['containerName'],member['loc']['kindModifiers']+' '+member['loc']['kind']])

			sublime.active_window().show_quick_panel(liste,self.on_done)
		except (Exception) as member:
			sublime.message_dialog("File navigation : plugin not yet intialize please retry after initialisation")

	def on_done(self,index):
		if index == -1: return
		view = sublime.active_window().active_view()
		view.show_at_center(self.regions[index])
		view.add_regions('typescript-definition', [self.regions[index]], 'comment', 'dot', sublime.DRAW_NO_FILL)


# CLOSE ALL PROJECTS
class TypescriptKill(sublime_plugin.TextCommand):

	def run(self, edit, characters=None):
		TSS.kill()


# OPEN ERROR PANEL
class TypescriptErrorPanel(sublime_plugin.TextCommand):

	def run(self, edit, characters=None):
		views = []
		liste = []
		errors = TSS.get_panel_errors(self.view)
		
		try:
			for e in errors:
				views.append(sublime.active_window().open_file(e['file'], sublime.TRANSIENT))

			if len(views) == 0: 
				liste.append('no errors')
				sublime.active_window().show_quick_panel(liste,self.on_done)
			else:
				self.open_panel(views,errors)

		except (Exception) as e:
			sublime.message_dialog("error panel : plugin not yet intialize please retry after initialisation")


	def open_panel(self,views,errors,i=0,dir=1):
		# LOADING
		if self.has_loading_views(views):
			before = i % 8
			after = (7) - before
			if not after:
				dir = -1
			if not before:
				dir = 1
			i += dir
			sublime.status_message(' Typescript Error panel is loading [%s=%s]' % \
				(' ' * before, ' ' * after))

			sublime.set_timeout(lambda: self.open_panel(views,errors,i,dir), 100)
			return

		# FINISHED LOADING
		sublime.status_message('')

		# OPEN PANEL
		self.files = []
		self.regions = []
		self.views = []
		liste = []
		count=0

		for e in errors:
			segments = e['file'].split('/')
			last = len(segments)-1
			filename = segments[last]
			view = views[count]

			start_line = e['start']['line']
			end_line = e['end']['line']
			left = e['start']['character']
			right = e['end']['character']

			a = view.text_point(start_line-1,left-1)
			b = view.text_point(end_line-1,right-1)

			file_info = filename + " Line " + str(start_line) + " - "
			title = self.error_text(e)
			description = file_info + view.substr(view.full_line(a)).strip()

			liste.append([title, description])
			self.regions.append( sublime.Region(a,b))
			self.files.append(e['file'])
			count = count+1

		sublime.active_window().show_quick_panel(liste,self.on_done)


	def has_loading_views(self,views):
		for view in views:
			if view.is_loading():
				return True

		return False


	def error_text(self,error):
		text = error['text']
		text = re.sub(r'^.*?:\s*', '', text)
		return text


	def on_done(self,index):
		if index == -1: return
		
		view = sublime.active_window().open_file(self.files[index])
		self.open_view(view,self.regions[index])
		

	def open_view(self,view,region):
		if view.is_loading():
			sublime.set_timeout(lambda: self.open_view(view,region), 100)
			return
		else:
			sublime.active_window().focus_view(view)
			view.show(region)


# AUTO COMPLETION
class TypescriptComplete(sublime_plugin.TextCommand):

	def run(self, edit, characters):
		for region in self.view.sel():
			self.view.insert(edit, region.end(), characters)

		TSS.update(self.view)
		TSS.interface = (characters==':')

		self.view.run_command('auto_complete',{
			'disable_auto_insert': True,
			'api_completions_only': True,
			'next_competion_if_showing': True
		})


# --------------------------------------- EVENT LISTENERS -------------------------------------- #

class TypescriptEventListener(sublime_plugin.EventListener):

	pending = 0
	settings = None

	def on_activated_async(self,view):
		self.init_view(view)
		

	def on_clone_async(self,view):
		self.init_view(view)


	def init_view(self,view):
		self.settings = sublime.load_settings('Typescript.sublime-settings')
		init(view)
		TSS.errors(view)


	def on_post_save_async(self,view):
		if not is_ts(view):
			return

		TSS.update(view)
		TSS.errors(view)

	
	def on_selection_modified_async(self, view):
		if not is_ts(view):
			return

		view.erase_regions('typescript-definition')
		TSS.set_error_status(view)


	def on_modified_async(self,view):
		if view.is_loading(): return
		if not is_ts(view):
			return

		TSS.update(view)
		self.pending = self.pending + 1

		if self.settings == None:
			self.settings = sublime.load_settings('Typescript.sublime-settings')

		if not self.settings.get('error_on_save_only'):
			sublime.set_timeout_async(lambda:self.handle_timeout(view),180)


	def handle_timeout(self,view):
		self.pending = self.pending -1
		if self.pending == 0:
			TSS.errors(view)


	def on_query_completions(self, view, prefix, locations):
		if is_ts(view):
			pos = view.sel()[0].begin()
			(line, col) = view.rowcol(pos)
			is_member = str(is_member_completion(view.substr(sublime.Region(view.line(pos-1).a, pos)))).lower()
			TSS.complete(view,line,col,is_member)

			return (COMPLETION_LIST, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)


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

	if is_dts(view):
		update_dts(filename)
		return
	
	root = get_root()
	added = None
	if root != None:
		if root != filename: added = filename
		filename = root

	TSS.start(view,filename,added)


def update_dts(filename):
	if filename.endswith('lib.d.ts'):
		return

	for root_file in ROOT_FILES:
		TSS.start(root_file,root_file.file_name(),filename)


def get_root():
	project_settings = sublime.active_window().active_view().settings().get('typescript')
	current_folder = os.path.dirname(sublime.active_window().active_view().file_name())
	top_folder =  get_top_folder(current_folder)
	top_folder_segments = top_folder.split(os.sep)

	# WITH PROJECT SETTINGS TYPESCRIP DEFINED
	if(project_settings != None):
			
		for root in project_settings:
			root_path = os.sep.join(top_folder_segments[:len(top_folder_segments)-1]+root.replace('\\','/').split('/'))
			root_dir = os.path.dirname(root_path)
			if current_folder.lower().startswith(root_dir.lower()):
				return root_path
			
		return None

	# SUBLIME TS ?
	else:

		segments = current_folder.split(os.sep)
		segments[0] = top_folder.split(os.sep)[0]
		length = len(segments)
		segment_range =reversed(range(0,length+1))

		for index in segment_range:
			folder = os.sep.join(segments[:index])
			config_file = os.path.join(folder,'.sublimets')
			config_data = get_data(config_file)
			if config_data != None:
				return os.path.join(folder,config_data['root'])

		return None
	


def get_top_folder(current_folder):
	top_folder = None
	open_folders = sublime.active_window().folders()
	for folder in open_folders:
		if current_folder.lower().startswith(folder.lower()):
			top_folder = folder
			break

	if top_folder != None:
		return top_folder
	
	return current_folder


def get_data(file):
	if os.path.isfile(file): 
		try: 
			f = open(file,'r').read()
			return json.loads(f)
		except IOError: 
			pass

	return None


# ---------------------------------------- PLUGIN LOADED --------------------------------------- #

def plugin_loaded():
	sublime.set_timeout(lambda:init(sublime.active_window().active_view()), 300)