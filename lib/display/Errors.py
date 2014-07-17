# coding=utf8

import sublime
import json

from .ErrorsHighlighter import ERRORSHIGHLIGHTER
from ..Tss import TSS
from ..Utils import max_calls
from ..system.Liste import get_root

# --------------------------------------- ERRORS -------------------------------------- #

class Errors(object):
	def __init__(self):
		pass

	@max_calls()
	def start_recalculation(self, file_name=""):
		if file_name == "" or file_name is None:
			file_name = sublime.active_window.active_view().file_name() # guess
		if get_root(file_name) is not None:
			# file_name is only needed to find root file
			TSS.errors(file_name, self.on_results)

	@max_calls()
	def on_results(self, errors, filename):
		""" this is the callback from the async process if new errors have been calculated """
		try:
			errors = json.loads(errors)
			if type(errors) is not list:
				raise Warning("tss.js internal error: %s" % errors)
			ERRORSHIGHLIGHTER.highlight(errors)
			sublime.active_window().run_command('typescript_error_panel_set_text', {"errors": errors} )
		except BaseException as e:
			ERRORSHIGHLIGHTER.highlight([])
			sublime.active_window().run_command('typescript_error_panel_set_text', {"errors": "%s" % e} )
			print('show_errors json error : %s (Exception Message: %s)' % (errors, "%s" % e))
		

	@max_calls()
	def on_close_typescript_project(self, root):
		""" Will be called when a typescript project is closed (eg all files closed).
			But there may be other open typescript projects.
			-> for future use :) """
		pass


# --------------------------------------- INIT -------------------------------------- #

ERRORS = Errors()
