# coding=utf8

from subprocess import Popen, PIPE
from threading import Thread
try:
	from queue import Queue
except ImportError:
	from Queue import Queue

import sublime
import subprocess
import json
import os
import re

from .Utils import debounce, dirname, encode, get_node, get_root, is_ts, is_dts, ST3
from .View import VIEW
from .Message import MESSAGE



# --------------------------------------- CONSTANT -------------------------------------- #
if os.name == 'nt':
	ICONS_PATH = ".."+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-illegal')
else:
	ICONS_PATH = "Packages"+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-illegal.png')

TSS_PATH =  os.path.join(dirname,'bin','tss.js')
COMPLETION_LIST = []
ROOT_FILES = []
FILES = {}
PROCESSES = {}
ERRORS = {}
PREFIXES = {
	'method': u'○',
	'property': u'●',
	'class':u'♦',
	'interface':u'◊',
	'keyword':u'∆',
	'constructor':u'■',
	'variable': u'V',
	'public':u'[pub]',
	'private':u'[priv]'
}

# --------------------------------------- TSS -------------------------------------- #
class Tss(object):

	interface = False
	methods = False

	threads = []
	processes = {}
	queues = {}

	# INTERFACE COMPLETION ?
	def get_interface_completion(self,value):
		self.interface = value

	# METHOD COMPLETION ?
	def get_method_completion(self,value):
		self.methods = value

	# GET PREFIXES
	def get_prefix(self,name):
		return PREFIXES[name] if name in PREFIXES else ""


	# GET PROCESS
	def get_process(self,view,error=False):
		filename = view.file_name();
		if filename in self.processes:
			return self.processes[filename]

		return None

	# CHECK IF ALL OPENED VIEWS HAVE A PROCESS ATTACHE
	def set_process(self,view,process):
		views = sublime.active_window().views()
		files = self.files(view)
		for v in views:
			filename = v.file_name() 
			if is_ts(filename) and not is_dts(filename) and filename in self.processes and filename in files:
				print(filename)
				if self.processes[filename] == None:
					self.processes[filename] == process


	# START PROCESS
	def start(self,view,filename,added,done=None):
		if filename in self.processes:
			if added != None and added not in self.processes:
				FILES[added] = filename
				self.processes[added] = self.processes[filename]
				self.queues[added] = self.queues[filename]
				self.update(view)

			if added in self.processes and self.processes[added] == None:
				self.processes[added] = self.processes[filename]
				self.queues[added] = self.queues[filename]
				
			return

		self.processes[filename] = None
		self.queues[filename] = {'stdin':Queue(),'stdout':Queue()}
		if added != None: 
			self.queues[added] = self.queues[filename]
			FILES[added] = filename
		
		FILES[filename] = filename
		thread = TssInit(filename,self.queues[filename]['stdin'],self.queues[filename]['stdout'])
		self.add_thread(thread)
		self.handle_threads(view,filename,added,done)


	# RELOAD PROCESS
	def reload(self,view):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(encode('reload\n'))
		print(process.stdout.readline().decode('UTF-8'))
		self.errors_async(view)


	# GET INDEXED FILES
	def files(self,view):
		process = self.get_process(view)
		if process == None:
			return
		
		process.stdin.write(encode('files\n'));
		return json.loads(process.stdout.readline().decode('UTF-8'))


	# KILL PROCESS
	def kill(self,view):
		files = self.files(view)
		if not files: return

		views = sublime.active_window().views()
		for v in views:
			if v.file_name() == None: continue
			for f in files:
				if v.file_name().replace('\\','/').lower() == f.lower() and not is_dts(v):
					return

		processes = PROCESSES[FILES[view.file_name()]]
		for process in processes:
			process.stdin.write(encode('quit\n'))
			process.kill()

		to_delete = []
		for f in files:
			f = f.replace('/',os.sep).lower()
			for p in self.processes:
				if f == p.lower() or self.processes[p]==None:
					to_delete.append(p)
					
		for f in to_delete:
			if f in self.processes: del self.processes[f]
			if f in self.queues: del self.queues[f]
			if f in FILES: del FILES[f]
			for root in ROOT_FILES:
				if root.file_name()==f:
					ROOT_FILES.remove(root)
					break

		MESSAGE.show('TypeScript project close',True)


	# DUMP FILE
	def dump(self,view,output):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(encode('dump {0} {1}\n'.format(output,view.file_name().replace('\\','/'))))
		print(process.stdout.readline().decode('UTF-8'))


	# TYPE
	def type(self,view,line,col):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(encode('type {0} {1} {2}\n'.format(str(line+1),str(col+1),view.file_name().replace('\\','/'))))
		return json.loads(process.stdout.readline().decode('UTF-8'))


	# DEFINITION
	def definition(self,view,line,col):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(encode('definition {0} {1} {2}\n'.format(str(line+1),str(col+1),view.file_name().replace('\\','/'))))
		return json.loads(process.stdout.readline().decode('UTF-8'))


	# REFERENCES
	def references(self,view,line,col):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(encode('references {0} {1} {2}\n'.format(str(line+1),str(col+1),view.file_name().replace('\\','/'))))
		return json.loads(process.stdout.readline().decode('UTF-8'))


	# STRUCTURE
	def structure(self,view):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(encode('structure {0}\n'.format(view.file_name().replace('\\','/'))))
		return json.loads(process.stdout.readline().decode('UTF-8'))


	# ASK FOR COMPLETIONS
	def complete(self,view,line,col,member):
		process = self.get_process(view)
		if process == None:
			return

		process.stdin.write(encode('completions {0} {1} {2} {3}\n'.format(member,str(line+1),str(col+1),view.file_name().replace('\\','/'))))
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
		process.stdin.write(encode('update nocheck {0} {1}\n'.format(str(lineCount+1),view.file_name().replace('\\','/'))))
		process.stdin.write(encode(content+'\n'))
		process.stdout.readline().decode('UTF-8')

	# REFACTOR UPDATE
	def refactor_update(self,root,filename,lines,content):
		if root in self.processes:
			process = self.processes[root]
			process.stdin.write(encode('update nocheck {0} {1}\n'.format(str(lines),filename)))
			process.stdin.write(encode(content+'\n'))
			process.stdout.readline().decode('UTF-8')

			self.queues[root]['stdin'].put(encode('update nocheck {0} {1}\n'.format(str(lines),filename)))
			self.queues[root]['stdin'].put(encode(content+'\n'))
			self.queues[root]['stdin'].put(encode('showErrors\n'))


	# UPDATE DEFINITION FILE
	def update_dts(self,filename):
		if filename.endswith('lib.d.ts'):
			return

		for root_file in ROOT_FILES:
			self.start(root_file,root_file.file_name(),filename)


	# ASYNC ERRORS
	def errors_async(self,view):
		if self.get_process(view) == None:
			return

		filename = view.file_name()
		(lineCount, col) = view.rowcol(view.size())
		content = view.substr(sublime.Region(0, view.size()))
		self.queues[filename]['stdin'].put(encode('update nocheck {0} {1}\n'.format(str(lineCount+1),filename.replace('\\','/'))))
		self.queues[filename]['stdin'].put(encode(content+'\n'))
		self.queues[filename]['stdin'].put(encode('showErrors\n'))


	# ADD THREADS
	def add_thread(self,thread):
		self.threads.append(thread)
		thread.daemon = True
		thread.start()

	
	#HANDLE THREADS
	def handle_threads(self,view,filename,added,done,i=0,dir=1):
		next_threads = []

		for thread in self.threads:
			if thread.is_alive():
				next_threads.append(thread)
				continue

			ROOT_FILES.append(view)
			self.processes[filename] = thread.process
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

			if not ST3:
				MESSAGE.repeat('Typescript is initializing')
				sublime.status_message(' Typescript is initializing [%s=%s]' % \
					(' ' * before, ' ' * after))
			else:
				MESSAGE.repeat(' Typescript is initializing [%s=%s]' % \
					(' ' * before, ' ' * after))

			sublime.set_timeout(lambda: self.handle_threads(view,filename,added,done,i,dir), 100)
			return

		(head,tail) = os.path.split(get_root())
		MESSAGE.show('TypeScript intialized for root file : '+tail,True)
		debounce(TSS.errors_async, 0.3, 'errors' + str(id(TSS)), view)
		debounce(done,0.3,'done')		
	

	# COMPLETIONS LIST
	def prepare_completions_list(self,entries):
		del COMPLETION_LIST[:]
		
		for entry in entries:
			if self.interface and entry['kind'] != 'primitive type' and entry['kind'] != 'interface' : continue
			key = self.get_completions_list_key(entry)
			value = self.get_completions_list_value(entry)
			COMPLETION_LIST.append((key,value))

		COMPLETION_LIST.sort()


	def get_completions_list_key(self,entry):
		kindModifiers = self.get_prefix(entry['kindModifiers'])
		kind = self.get_prefix(entry['kind'])

		return kindModifiers+' '+kind+' '+str(entry['name'])+' '+str(entry['type'])


	def get_completions_list_value(self,entry):
		match = re.match('(<.*>|)\((.*)\):',str(entry['type']))
		result = []

		if match:
			variables = self.parse_args(match.group(2))
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

			return entry['name']+'('+','.join(result)+');'
		else:
			return entry['name']

	def parse_args(self,group):
		args = []
		arg = ""
		callback = False

		for char in group:
			if char == '(':
				arg += char
				callback = True
			elif char == ')':
				arg += char
				callback = False
			elif char == ',':
				if callback == False:
					args.append(arg)
					arg = ""
			else:
				arg+=char

		args.append(arg)
		return args

		
	def get_completions_list(self):
		return COMPLETION_LIST


	# ERRORS
	def show_errors(self,view,errors):
		try:
			errors = json.loads(errors)
			self.highlight_errors(view,errors)
			if VIEW.has_error: sublime.active_window().run_command('typescript_error_panel_view',{"errors":errors})
		except:
			print('show_errors json error : ',errors)


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
		Thread.__init__(self)

	def run(self):
		node = get_node()
		kwargs = {}
		if os.name == 'nt':
			errorlog = open(os.devnull, 'w')
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			kwargs = {'stderr':errorlog, 'startupinfo':startupinfo}

		print('typescript initializing')

		self.process = Popen([node, TSS_PATH ,self.filename], stdin=PIPE, stdout=PIPE, **kwargs)
		p = Popen([node, TSS_PATH ,self.filename], stdin=PIPE, stdout=PIPE, **kwargs)
		PROCESSES[self.filename] = [self.process,p]

		self.process.stdout.readline().decode('UTF-8')
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
				if ST3: 
					TSS.show_errors(sublime.active_window().active_view(),line)
				else: 
					sublime.set_timeout(lambda: TSS.show_errors(sublime.active_window().active_view(),line), 1)

		self.stdout.close()



# --------------------------------------- INITIALISATION -------------------------------------- #

TSS = Tss()