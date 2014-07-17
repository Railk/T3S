# coding=utf8

import sublime
import sublime_plugin

from .display.T3SViews import T3SVIEWS
from .display.Completion import COMPLETION
from .display.Errors import ERRORS
from .display.ErrorsHighlighter import ERRORSHIGHLIGHTER
from .system.Files import FILES
from .system.Liste import LISTE
from .system.Processes import PROCESSES
from .system.Settings import SETTINGS
from .Tss import TSS
from .Utils import debounce, is_ts, is_dts, read_file, get_file_infos, ST3, Debug, max_calls, run_command_on_any_ts_view


# ------------------------------------------- INIT ------------------------------------------ #
c = [0]

@max_calls(name='main init')
def init(view):
	c[0] = c[0] + 1
	if c[0] == 10:
		pass #import spdb ; spdb.start()


	if not is_ts(view) or is_dts(view):
		return
	if read_file(view.file_name()) is None:
		return

	root = SETTINGS.get_root(view)
	if root == 'no_ts' or root == None: return

	filename = view.file_name()
	if PROCESSES.is_initialized(root):
		filename, num_lines, content = get_file_infos(view)
		if LISTE.has(filename):
			TSS.update(filename, num_lines, content)
		else:
			FILES.add(root, filename)
			TSS.add(root, filename, num_lines, content)

		view.run_command('typescript_update_structure')

	elif not PROCESSES.initialisation_started(root):
		FILES.add(root,filename)
		if filename != root:
			FILES.add(root,root)
		TSS.addEventListener('init', root, on_init)
		TSS.addEventListener('kill', root, on_kill)
		TSS.init(root)
		view.settings().set('auto_complete', SETTINGS.get("auto_complete"))
		view.settings().set('extensions', ['ts'])
		
@max_calls()
def on_init(root):
	TSS.removeEventListener('init', root, on_init)
	FILES.init(root, on_files_loaded)

@max_calls()
def on_files_loaded():
	# we don't know if a ts view is activated, start conditions
	run_command_on_any_ts_view('typescript_update_structure', {"force": True})
	run_command_on_any_ts_view('typescript_recalculate_errors')


@max_calls()
def on_kill(root):
	TSS.removeEventListener('kill', root, on_kill)
	FILES.remove_by_root(root)
	ERRORS.on_close_typescript_project(root)
	T3SVIEWS.hide_all()




# ----------------------------------------- LISTENERS ---------------------------------------- #

class TypescriptEventListener(sublime_plugin.EventListener):


	# CLOSE FILE
	@max_calls(name='Listener.on_close')
	def on_close(self, view):

		if is_ts(view) and not is_dts(view):
			filename = view.file_name()
			if ST3: TSS.kill(filename)
			else: sublime.set_timeout(lambda:TSS.kill(filename),300)


	# FILE ACTIVATED
	@max_calls()
	def on_activated(self, view):
		init(view)

		
	# ON CLONED FILE
	@max_calls()
	def on_clone(self, view):
		init(view)


	# ON SAVE
	@max_calls()
	def on_post_save(self, view):
		if not is_ts(view):
			return

		filename, num_lines, content = get_file_infos(view)
		if LISTE.has(filename):
			TSS.update(filename, num_lines, content)
			FILES.update(filename, num_lines, content, True)

		view.run_command('typescript_update_structure', {"force": True})
		ERRORS.start_recalculation(view.file_name())

		if SETTINGS.get('build_on_save'):
			sublime.active_window().run_command('typescript_build',{"characters":False})


	# ON CLICK
	@max_calls(name='listener.on_selection_modified')
	def on_selection_modified(self, view):
		if not is_ts(view) or is_dts(view):
			return

		ERRORSHIGHLIGHTER.display_error_in_status_if_cursor(view)
		view.erase_regions('typescript-definition')
		view.erase_regions('typescript-error-hint')


	# ON VIEW MODIFIED
	@max_calls()
	def on_modified(self, view):
		if view.is_loading():
			return
		if not is_ts(view) or is_dts(view):
			return

		filename, num_lines, content = get_file_infos(view)
		if LISTE.has(filename):
			TSS.update(filename, num_lines, content)
			FILES.update(filename, num_lines, content)

		view.run_command('typescript_update_structure', {"force": True})
		COMPLETION.trigger(view, TSS)

		if not SETTINGS.get('error_on_save_only'):
			ERRORS.start_recalculation(view.file_name())


	# ON QUERY COMPLETION
	def on_query_completions(self, view, prefix, locations):
		pos = view.sel()[0].begin()
		(line, col) = view.rowcol(pos)
		Debug('autocomplete', "on_query_completions(), sublime wants to see the results, cursor currently at %i , %i (enabled: %s, items: %i)" % (line+1, col+1, COMPLETION.enabled_for['viewid'], len(COMPLETION.get_list()) ) )
		if is_ts(view) and not is_dts(view):
			if COMPLETION.enabled_for['viewid'] == view.id():
				COMPLETION.enabled_for['viewid'] = -1 # receive only once
				return (COMPLETION.get_list(), sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)


	# ON QUERY CONTEXT (execute commandy only on .ts files)
	def on_query_context(self, view, key, operator, operand, match_all):
		if key == "T3S":
			view = sublime.active_window().active_view()
			return is_ts(view)
			
			
