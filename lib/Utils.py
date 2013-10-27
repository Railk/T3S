# coding=utf8

import sublime
import threading
import subprocess
import os
import re
import json


# PACKAGE PATH
dirname = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))


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