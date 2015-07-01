# coding=utf8

import sublime
import threading
import subprocess
import os
import re
import json
import codecs
import hashlib
import sys

DEFAULT_DEBOUNCE_DELAY = 0.8

print_classifications = []
# possible classifications:
possible_classifications = [ 'all',
	'tss', 'tss+', 'tss++',
	'command', 'command+',
	'adapter', 'adapter+',
	'files',
	'build', 'build+',
	'structure',
	'autocomplete',
	'errorpanel', 'errorpanel+',
	'focus', 'max_calls',
	'layout',
	'goto']

# DEBUG
def Debug(classification, text):
	if 'all' in print_classifications or classification in print_classifications:
		print("T3S: %s: %s" % (classification.ljust(8), text))
	if classification not in possible_classifications:
		print("T3S: debug: got unknown debug message classification: %s. " \
			"Consider adding this to possible_classifications" % classification)
	sys.stdout.flush()

# HELPER to hunt down memory leak
from functools import wraps
def max_calls(limit = 1500, name=""):
	"""Decorator which allows its wrapped function to be called `limit` times"""
	def decorator(func):
		# Disable limit:
		return func
		@wraps(func)
		def wrapper(*args, **kwargs):
			calls = getattr(wrapper, 'calls', 0)
			calls += 1
			setattr(wrapper, 'calls', calls)
			fname = name if name != "" else func.__name__

			if calls == limit + 1:
				Debug('max_calls', "LIMIT !! ## !!: Fkt %s has %i calls, stop" % (fname, calls - 1))

			if calls >= limit + 1:
				return None

			Debug('max_calls', "CALL: Fkt %s has %i calls -> +1" % (fname, calls - 1))

			return func(*args, **kwargs)
		setattr(wrapper, 'calls', 0)
		return wrapper
	return decorator


# CANCEL COMMAND EXCEPTION
class CancelCommand(Exception):
	pass
	
# CANCEL COMMAND EXCEPTION CATCHER DECORATOR
def catch_CancelCommand(func):
	def catcher(*kargs, **kwargs):
		try:
			func(*kargs, **kwargs)
		except CancelCommand:
			Debug('command', "A COMMAND WAS CANCELED")
			pass
	return catcher

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
	'private':u'[priv]',
	'getter':u'<',
	'setter':u'>'
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

# TS VIEW
def get_any_ts_view():
	v = sublime.active_window().active_view()
	if is_ts(v) and not is_dts(v):
		return v
	for w in sublime.windows():
		for v in w.views():
			if is_ts(v) and not is_dts(v):
				return v

def get_any_view_with_root(root):
	from .system.Liste import get_root
	v = sublime.active_window().active_view()
	if is_ts(v) and not is_dts(v) and get_root(v.file_name()) == root:
		return v
	for w in sublime.windows():
		for v in w.views():
			if is_ts(v) and not is_dts(v) and get_root(v.file_name()) == root:
				return v



# RUN COMMAND
def run_command_on_any_ts_view(command, args=None):
	v = get_any_ts_view()
	if v is not None:
		v.run_command(command, args)

# IS A TYPESCRIPT FILE
def is_ts(view):
	if view is None:
		return False
	fn = view.file_name()
	fn2 = view.file_name()
	fn3 = view.file_name()
	if fn is None or fn2 is None:
		return False
	if fn is None or fn2 is None or fn3 is None:
		pass
		#import spdb ; spdb.start()
	return fn.endswith('.ts')


# IS A TYPESCRIPT DEFINITION FILE
def is_dts(view):
	return view.file_name() and view.file_name().endswith('.d.ts')


# IS AN OBJECT MEMBER 
# TRUE: line=Instance. or line=Instance.fooba or line=Instance.foobar.alic
# FALSE: line=Inst
js_id_re = re.compile(u'^[_$a-zA-Z\u00FF-\uFFFF][_$a-zA-Z0-9\u00FF-\uFFFF]*')
def is_member_completion(line_text):
	def partial_completion():
		sp = line_text.split(".")
		if len(sp) > 1:
			return js_id_re.match(sp[-1]) is not None
		return False
	return line_text.endswith(".") or partial_completion()

def get_col_after_last_dot(line_text):
	return line_text.rfind(".") + 1


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

# READ FILE
def read_file(filename):
	""" returns None or file contents if available """
	filename = os.path.normcase(filename) # back to \\ in nt
	if os.path.isfile(filename):
		try:
			if os.name == 'nt':
				return open(filename, 'r', encoding='utf8').read()
			else:
				return codecs.open(filename, 'r', 'utf-8').read()
		except IOError:
			pass
	return None


def read_and_decode_json_file(filename):
	""" returns None or json-decoded file contents as object,list,... """
	f = read_file(filename)
	return json.loads(f) if f is not None else None

# FILE EXISTS
def file_exists(filename):
	""" returns weather the file exists """
	return os.path.isfile(os.path.normcase(filename))

# GET VIEW CONTENT
def get_content(view):
	return view.substr(sublime.Region(0, view.size()))

def get_content_of_line_at(view, pos):
	return view.substr(sublime.Region(view.line(pos-1).a, pos))


# GET LINES
def get_lines(view):
	(lines, col) = view.rowcol(view.size())
	return lines


# GET FILE INFO
def get_file_infos(view):
	return (view.file_name(), get_lines(view), get_content(view))
	
# MAKE MD5 of disk contents of file
def hash_file(filename, blocksize=65536):
	f = open(filename)
	buf = f.read(blocksize)
	hasher = hashlib.md5()
	while len(buf) > 0:
		hasher.update(encode(buf))
		buf = f.read(blocksize)
	f.close()
	return hasher.hexdigest()

# FILENAME transformations
def filename2linux(filename):
	""" returns filename with linux slashes """
	return filename.replace('\\','/')

def filename2key(filename):
	""" returns the unified version of filename which can be used as dict key """
	return filename2linux(filename).lower()

def fn2k(filename):
	""" shortcut for filename2key """
	return filename2key(filename)

def fn2l(filename):
	""" shortcut for filename2linux """
	return filename2linux(filename)


