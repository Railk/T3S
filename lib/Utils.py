# coding=utf8

import sublime
import threading
import subprocess
import sys
import os
import re
import json


# PACKAGE PATH
dirname = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))


# NODE SETTINGS
node_path_settings = sublime.load_settings('T3S.sublime-settings').get("node_path")


# VERSIONS
version = int(sublime.version())
ST3 = int(sublime.version()) >= 3000


# MEMBER PREFIX
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

def get_prefix(token):
	if token in PREFIXES:
		return PREFIXES[token]
	else:
		return ''


# GET TSS PATH
def get_tss():
	return os.path.join(dirname,'bin','tss.js')


# NODE PATH
def get_node():
	if ST3: node_path = sublime.load_settings('T3S.sublime-settings').get("node_path")
	else : node_path = node_path_settings

	if node_path == 'none':
		return '/usr/local/bin/node' if sys.platform == "darwin" else 'node'
	else:
		return node_path+'/node'


# GET PROCESS KWARGS
def get_kwargs():
	if os.name == 'nt':
		errorlog = open(os.devnull, 'w')
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		return {'stderr':errorlog, 'startupinfo':startupinfo}
	else:
		return {}


# BYTE ENCODE
def encode(message):
	if ST3: return bytes(message,'UTF-8')
	else: return message.encode('UTF-8')


# IS A TYPESCRIPT FILE
def is_ts(view):
	if not view: return False
	return view.file_name() and view.file_name().endswith('.ts')


# IS A TYPESCRIPT DEFINITION FILE
def is_dts(view):
	return view.file_name() and view.file_name().endswith('.d.ts')


# IS AN OBJECT MEMBER
js_id_re = re.compile(u'^[_$a-zA-Z\u00FF-\uFFFF][_$a-zA-Z0-9\u00FF-\uFFFF]*')
def is_member_completion(line):
	def partial_completion():
		sp = line.split(".")
		if len(sp) > 1:
			return js_id_re.match(sp[-1]) is not None
		return False
	return line.endswith(".") or partial_completion()


# DEBOUNCE CALL
debounced_timers = {}
def debounce(fn, delay, uid=None, *args):
	uid = uid if uid else fn

	if uid in debounced_timers:
		debounced_timers[uid].cancel()

	if ST3:
		timer = threading.Timer(delay, fn, args)
	else:
		args_safe = (fn,)+args
		timer = threading.Timer(delay, thread_safe, args_safe)
	timer.start()

	debounced_timers[uid] = timer

# ST2 THREAD SAFE
def thread_safe(fn,args=None):
	if args!= None: sublime.set_timeout(lambda:fn(args),0)
	else: sublime.set_timeout(lambda:fn(),0)


# GET PROJECT ROOT FILE
def get_root():
	if sublime.active_window().active_view().file_name() == None: return 'no_ts'
	project_settings = sublime.active_window().active_view().settings().get('typescript')
	current_folder = os.path.dirname(sublime.active_window().active_view().file_name())
	top_folder =  get_top_folder(current_folder)
	top_folder_segments = top_folder.split(os.sep)

	# WITH PROJECT SETTINGS TYPESCRIPT DEFINED
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
			config_data = get_data(config_file,True)
			if config_data != None:
				return os.path.join(folder,config_data['root'])

		return None
	

# GET SUBLIME OPEN FOLDERS
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


# GET FILE DATA
def get_data(file,decode=False):
	if os.path.isfile(file): 
		try: 
			f = open(file,'r').read()
			if decode: return json.loads(f)
			else: return f
		except IOError: 
			pass

	return None


# GET VIEW CONTENT
def get_content(view):
	return view.substr(sublime.Region(0, view.size()))


# GET LINES
def get_lines(view):
	(lines, col) = view.rowcol(view.size())
	return lines


# GET FILE INFO
def get_file_infos(view):
	return (view.file_name(),get_lines(view),get_content(view))