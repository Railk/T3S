# coding=utf8

import sublime
import sublime_plugin

from .display.View import VIEW
from .display.Completion import COMPLETION
from .display.Errors import ERRORS
from .display.Message import MESSAGE
from .system.Files import FILES
from .system.Liste import LISTE
from .system.Processes import PROCESSES
from .Tss import TSS
from .Utils import debounce, is_ts, is_dts, is_member_completion, get_root, get_data, get_file_infos, ST3


# ------------------------------------------- INIT ------------------------------------------ #

def init(view):
	if not is_ts(view): return
	if is_dts(view): return
	if get_data(view.file_name()) == None: return

	root = get_root()
	if root == 'no_ts': return
	if root == None: 
		MESSAGE.show('Cannot find root file please review you settings')
		return

	view.settings().set('auto_complete',True)
	view.settings().set('extensions',['ts'])

	process = PROCESSES.get(root)
	if process != None:
		if not process.is_alive():
			args = get_file_infos(view)
			filename = view.file_name()
			if LISTE.has(filename):
				TSS.update(*args)
			else:
				args = (root,)+args
				FILES.add(root,filename)
				TSS.add(*args)
	else:
		TSS.addEventListener('init',root,on_init)
		TSS.addEventListener('kill',root,on_kill)
		TSS.init(root)

def on_init(process):
	TSS.removeEventListener('init',process.root,on_init)
	FILES.init(process.root)
	ERRORS.init(process.root,process.r_async)
	VIEW.init()

def on_kill(process):
	TSS.removeEventListener('kill',process.root,on_kill)
	FILES.remove_by(process.root)
	ERRORS.remove(process.root)
	pass


# ----------------------------------------- LISTENERS ---------------------------------------- #

class TypescriptEventListener(sublime_plugin.EventListener):

	settings = None
	error_delay = 0.3


	# CLOSE FILE
	def on_close(self,view):
		if VIEW.is_view(view.name()): 
			VIEW.delete_view(view.name())

		if is_ts(view) and not is_dts(view):
			filename = view.file_name()
			if ST3: TSS.kill(filename)
			else: sublime.set_timeout(lambda:TSS.kill(filename),300)


	# FILE ACTIVATED
	def on_activated(self,view):
		self.init_view(view)

		
	# ON CLONED FILE
	def on_clone(self,view):
		self.init_view(view)


	# INIT NEW FILE
	def init_view(self,view):
		if not is_ts(view): return
		self.settings = sublime.load_settings('T3S.sublime-settings')
		init(view)
		VIEW.update()
		debounce(TSS.errors, self.error_delay, 'errors' + str(id(TSS)), *get_file_infos(view))


	# ON SAVE
	def on_post_save(self,view):
		if not is_ts(view):
			return

		args = get_file_infos(view)
		TSS.update(*args)
		VIEW.update()
		FILES.update(view,True)
		debounce(TSS.errors, self.error_delay, 'errors' + str(id(TSS)), *args)

		if self.settings == None:
			self.settings = sublime.load_settings('T3S.sublime-settings')

		if self.settings.get('build_on_save'):
			sublime.active_window().run_command('typescript_build',{"characters":False})


	# ON CLICK
	def on_selection_modified(self, view):
		if not is_ts(view):
			if VIEW.is_open_view(view.name()): VIEW.on_view(view)
			return

		filename = view.file_name()
		if not LISTE.has(filename) and get_data(filename) != None:
			root = get_root()
			if root == None or root == 'no_ts':return
			args = (root,)+get_file_infos(view)
			FILES.add(root,filename)
			TSS.add(*args)

		view.erase_regions('typescript-definition')
		ERRORS.set_status(view)


	# ON VIEW MODIFIED
	def on_modified(self,view):
		if view.is_loading(): return
		if not is_ts(view):
			return

		if self.settings == None:
			self.settings = sublime.load_settings('T3S.sublime-settings')

		args = get_file_infos(view)
		TSS.update(*args)
		FILES.update(view)
		VIEW.update()

		if not self.settings.get('error_on_save_only'):
			debounce(TSS.errors, self.error_delay, 'errors' + str(id(TSS)), *args)


	# ON QUERY COMPLETION
	def on_query_completions(self,view,prefix,locations):
		if is_ts(view):
			if COMPLETION.enabled:
				TSS.update(*get_file_infos(view))
				pos = view.sel()[0].begin()
				(line, col) = view.rowcol(pos)
				is_member = str(is_member_completion(view.substr(sublime.Region(view.line(pos-1).a, pos)))).lower()
				TSS.complete(view.file_name(),line,col,is_member)

				COMPLETION.enabled = False
				return (COMPLETION.get_list(), sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)


	# ON QUERY CONTEXT
	def on_query_context(self, view, key, operator, operand, match_all):
		if key == "T3S":
			view = sublime.active_window().active_view()
			return is_ts(view)