# coding=utf8

from threading import Thread
import sublime
import sublime_plugin
import os
import re
import traceback

from .commands.Compiler import Compiler
from .commands.Refactor import Refactor
from .display.T3SViews import T3SVIEWS
from .display.Errors import ERRORS
from .display.Message import MESSAGE
from .display.Completion import COMPLETION
from .system.Liste import LISTE, get_root
from .system.Settings import SETTINGS
from .Tss import TSS
from .Utils import read_file, get_file_infos, get_prefix, debounce, ST3, catch_CancelCommand, CancelCommand, Debug, max_calls


# AUTO COMPLETION
class TypescriptCompletion(sublime_plugin.TextCommand):
	
	def run(self, edit):
		COMPLETION.trigger(self.view, TSS, force_enable=True)


# RELOAD PROJECT
class TypescriptReloadProject(sublime_plugin.TextCommand):

	def run(self, edit):
		sublime.active_window().run_command('save_all')
		MESSAGE.show('Reloading project')
		TSS.reload(self.view.file_name(), lambda: MESSAGE.show('Reloading finished', True))


# SHOW INFOS
class TypescriptType(sublime_plugin.TextCommand):

	@catch_CancelCommand
	def run(self, edit):
		TSS.assert_initialisation_finished(self.view.file_name())

		if not ST3: return
		
		pos = self.view.sel()[0].begin()
		(_line, _col) = self.view.rowcol(pos)
		_view = self.view
		
		def async_react(types, filename, line, col):
			if types == None: return
			if 'kind' not in types: return

			# Only display type if cursor has not moved
			view = sublime.active_window().active_view()
			pos = view.sel()[0].begin()
			(_line, _col) = view.rowcol(pos)
			if col != _col or line != _line: return
			if view != _view: return

			kind = get_prefix(types['kind'])
			if types['docComment'] != '':
				liste = types['docComment'].split('\n')+[kind+' '+types['fullSymbolName']+' '+types['type']]
			else:
				liste = [kind+' '+types['fullSymbolName']+' '+types['type']]

			view.show_popup_menu(liste, None)
			
		# start async request
		TSS.type(self.view.file_name(), _line, _col, callback=async_react)



# GO TO DEFINITION
class TypescriptDefinition(sublime_plugin.TextCommand):

	@catch_CancelCommand
	def run(self, edit):
		TSS.assert_initialisation_finished(self.view.file_name())
		
		pos = self.view.sel()[0].begin()
		(_line, _col) = self.view.rowcol(pos)
		_view = self.view

		def async_react(definition, filename, line, col):
			if definition == None: return
			if 'file' not in definition: return

			# Only display type if cursor has not moved
			view = sublime.active_window().active_view()
			pos = view.sel()[0].begin()
			(_line, _col) = view.rowcol(pos)
			if col != _col or line != _line: return
			if view != _view: return

			view = sublime.active_window().open_file(definition['file'])
			self.open_view(view, definition)
			
		TSS.definition(self.view.file_name(), _line, _col, callback=async_react)

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

			Debug('focus', 'Z focus view %i' % view.id())
			sublime.active_window().focus_view(view)
			view.show_at_center(region)

			draw = sublime.DRAW_NO_FILL if ST3 else sublime.DRAW_OUTLINED
			view.add_regions('typescript-definition', [region], 'comment', 'dot', draw)


# BASIC REFACTORING
class TypescriptReferences(sublime_plugin.TextCommand):

	@catch_CancelCommand
	def run(self, edit):
		TSS.assert_initialisation_finished(self.view.file_name())
		
		pos = self.view.sel()[0].begin()
		(line, col) = self.view.rowcol(pos)
		_view = self.view
		
		def async_react(refs, filename, line, col):
			self.refs = refs
			self.window = sublime.active_window()

			if refs == None: return

			view = sublime.active_window().active_view()
			pos = view.sel()[0].begin()
			(_line, _col) = view.rowcol(pos)
			if col != _col or line != _line: return
			if view != _view: return

			refactor_member = ""
			try :
				for ref in refs:
					if ref['file'].replace('/',os.sep).lower() == self.view.file_name().lower():
						refactor_member = self.view.substr(self.get_region(self.view, ref['min'], ref['lim']))
				if(refactor_member):
					self.window.show_input_panel('Refactoring', refactor_member, self.on_done, None, None)
			except (Exception) as ref:
				sublime.status_message("error panel : plugin not yet intialize please retry after initialisation")

		TSS.references(self.view.file_name(), line, col, callback=async_react)

	def get_region(self,view,min,lim):
		start_line = min['line']
		end_line = lim['line']
		left = min['character']
		right = lim['character']

		a = view.text_point(start_line-1,left-1)
		b = view.text_point(end_line-1,right-1)
		return sublime.Region(a,b)

	def on_done(self,name):
		refactor = Refactor(self.window,name,self.refs)
		refactor.daemon = True
		refactor.start()


# OPEN OUTLINE PANEL (via shortkey / public command)
class TypescriptStructure(sublime_plugin.TextCommand):
	""" this command opens and focus the structure/outline view """
	@catch_CancelCommand
	@max_calls(name='TypescriptStructure')
	def run(self, edit_token):
		Debug('structure', 'open view if not already open')
		TSS.assert_initialisation_finished(self.view.file_name())

		T3SVIEWS.OUTLINE.enable()
		T3SVIEWS.OUTLINE.bring_to_top(back_to=self.view)

		self.view.run_command('typescript_update_structure', {"force": True})
	

# REFRESH OUTLINE VIEW to match CURRENT VIEW
class TypescriptUpdateStructure(sublime_plugin.TextCommand):
	@catch_CancelCommand
	@max_calls(name='TypescriptUpdateStructure')
	def run(self, edit_token, force=False):
		TSS.assert_initialisation_finished(self.view.file_name())

		def async_react(members, filename, sender_view_id):
			## members is the already json-decoded tss.js answer
			Debug('structure', 'STRUCTURE async_react for %s in start view %s, now view %s' 
					% (filename, self.view.id(), sublime.active_window().active_view().id()) )

			if sublime.active_window().active_view().id() != sender_view_id or self.view.id() != sender_view_id:
				Debug('structure', 'STRUCTURE async_react canceled because of view change')
				return

			self.view.run_command('typescript_outline_view_set_text', {"members": members} )


		if T3SVIEWS.OUTLINE.is_active() and (force or not T3SVIEWS.OUTLINE.is_current_ts(self.view)):
			Debug('structure', 'STRUCTURE for %s in view %s, active view is %s' 
				% (self.view.file_name(), self.view.id(), sublime.active_window().active_view().id()))
			TSS.structure(self.view.file_name(), self.view.id(), async_react)


# OPEN and WRITE TEXT TO OUTLINE VIEW
class TypescriptOutlineViewSetText(sublime_plugin.TextCommand):
	@max_calls(name='TypescriptOutlineViewSetText')
	def run(self, edit_token, members):
		#try: # for debugging ok, but TODO: reinsert try
			Debug('structure', 'STRUCTURE update outline view panel')
			T3SVIEWS.OUTLINE.set_text(edit_token, members, self.view)
		#except (Exception) as e:
		#	sublime.status_message("Outline panel : %s" % e)
		#	print("Outline panel: %s" % e)


# OPEN ERROR PANEL (via shortkey / public command)
class TypescriptErrorPanel(sublime_plugin.TextCommand):

	@catch_CancelCommand
	@max_calls(name='TypescriptErrorPanel')
	def run(self, edit_token):
		TSS.assert_initialisation_finished(self.view.file_name())

		T3SVIEWS.ERROR.enable(edit_token)
		T3SVIEWS.ERROR.bring_to_top(back_to=self.view)

		self.view.run_command('typescript_recalculate_errors')




# REFRESH ERRORS (eg after typing characters, if not automatically done)
class TypescriptRecalculateErrors(sublime_plugin.TextCommand):

	@catch_CancelCommand
	@max_calls(name='TypescriptRecalculateErrors')
	def run(self, edit_token):
		TSS.assert_initialisation_finished(self.view.file_name())
		TSS.update(*get_file_infos(self.view))
		ERRORS.start_recalculation(self.view.file_name())


class TypescriptErrorPanelSetText(sublime_plugin.TextCommand):
	@max_calls(name='TypescriptErrorPanelSetText')
	def run(self, edit_token, errors):
		#try: # for debugging ok, but TODO: reinsert try
			T3SVIEWS.ERROR.set_text(edit_token, errors)
		#except (Exception) as e:
		#	sublime.status_message("Error panel : %s" % e)
		#	print("Error panel: %s" % e)


class TypescriptSetErrorCalculationStatusMessage(sublime_plugin.TextCommand):
	@max_calls(name='TypescriptSetErrorCalculationStatusMessage')
	def run(self, edit_token, message):
		T3SVIEWS.ERROR.set_error_calculation_status_message(edit_token, message)


# COMPILE VIEW
class TypescriptBuild(sublime_plugin.TextCommand):

	@catch_CancelCommand
	def run(self, edit, characters):
		if not SETTINGS.get('activate_build_system'):
			print("T3S: build_system_disabled")
			return
		filename = self.view.file_name()
		TSS.assert_initialisation_finished(filename)
		
		self.window = sublime.active_window()
		if characters != False:
			self.window.run_command('save')

		compiler = Compiler(self.window, get_root(filename), filename)
		compiler.daemon = True
		compiler.start()
		
		sublime.status_message('Compiling : ' + filename)
			

class TypescriptBuildView(sublime_plugin.TextCommand):
	
	def run(self, edit_token, filename):		
		if filename != 'error':
			if SETTINGS.get('show_build_file'):
				T3SVIEWS.COMPILE.enable()
				T3SVIEWS.COMPILE.bring_to_top(back_to=self.view)
				if os.path.exists(filename):
					data = read_file(filename)
					T3SVIEWS.COMPILE.set_text(edit_token, data)
				else:
					T3SVIEWS.COMPILE.set_text(edit_token, filename)





