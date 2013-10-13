# coding=utf8

import sublime
import sublime_plugin

from .Utils import debounce, is_ts, is_dts, is_member_completion, get_root, ST3
from .View import VIEW
from .Tss import TSS



# INIT
def init(view):
	if not is_ts(view): return

	filename = view.file_name()
	view.settings().set('auto_complete',False)
	view.settings().set('extensions',['ts'])

	if is_dts(view):
		TSS.update_dts(filename)
		return
	
	root = get_root()
	if root == 'no_ts': return

	added = None
	if root != None:
		if root != filename: added = filename
		filename = root

	TSS.start(view,filename,added,on_done_init)
	VIEW.init()

def on_done_init():
	if VIEW.is_open_view('Typescript : Outline View'): sublime.active_window().run_command('typescript_structure')
	if VIEW.is_open_view('Typescript : Errors List'): sublime.active_window().run_command('typescript_error_panel')



# LISTENERS
class TypescriptEventListener(sublime_plugin.EventListener):

	settings = None
	error_delay = 0.3

	def on_close(self,view):
		if VIEW.is_view(view.name()): 
			VIEW.delete_view(view.name())

		if is_ts(view):
			if ST3: TSS.kill(view)
			else: sublime.set_timeout(lambda:TSS.kill(view),300)


	def on_activated(self,view):
		self.init_view(view)
		

	def on_clone(self,view):
		self.init_view(view)


	def init_view(self,view):
		if not is_ts(view): return
		self.settings = sublime.load_settings('T3S.sublime-settings')
		init(view)
		debounce(TSS.errors_async, self.error_delay, 'errors' + str(id(TSS)), view)
		if VIEW.is_open_view('Typescript : Outline View'): sublime.active_window().run_command('typescript_structure')


	def on_post_save(self,view):
		if not is_ts(view):
			return

		TSS.update(view)
		debounce(TSS.errors_async, self.error_delay, 'errors' + str(id(TSS)), view)
		if VIEW.is_open_view('Typescript : Errors List'): sublime.active_window().run_command('typescript_error_panel')

		if self.settings == None:
			self.settings = sublime.load_settings('T3S.sublime-settings')

		if self.settings.get('build_on_save'):
			sublime.active_window().run_command('typescript_build',
				{
					"characters":False
				}
			)

	
	def on_selection_modified(self, view):
		if not is_ts(view):
			if VIEW.is_open_view(view.name()): VIEW.on_view(view)
			return

		view.erase_regions('typescript-definition')
		TSS.set_error_status(view)


	def on_modified(self,view):
		if view.is_loading(): return
		if not is_ts(view):
			return

		if self.settings == None:
			self.settings = sublime.load_settings('T3S.sublime-settings')

		TSS.update(view)
		if VIEW.is_open_view('Typescript : Outline View'): sublime.active_window().run_command('typescript_structure')
		if VIEW.is_open_view('Typescript : Errors List'): sublime.active_window().run_command('typescript_error_panel')

		if not self.settings.get('error_on_save_only'):
			debounce(TSS.errors_async, self.error_delay, 'errors' + str(id(TSS)), view)


	def on_query_completions(self, view, prefix, locations):
		if is_ts(view):
			pos = view.sel()[0].begin()
			(line, col) = view.rowcol(pos)
			is_member = str(is_member_completion(view.substr(sublime.Region(view.line(pos-1).a, pos)))).lower()
			TSS.complete(view,line,col,is_member)

			return (TSS.get_completions_list(), sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)


	def on_query_context(self, view, key, operator, operand, match_all):
		if key == "T3S":
			view = sublime.active_window().active_view()
			return is_ts(view)