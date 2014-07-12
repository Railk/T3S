# coding=utf8

from threading import Thread

import sublime
import os
import json

from .Views import VIEWS
from ..Tss import TSS
from ..Utils import dirname, debounce, ST3, fn2k, is_ts

# --------------------------------------- ERRORS -------------------------------------- #

class Errors(object):

	errors = {}

	underline = sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_EMPTY_AS_OVERWRITE

	def __init__(self):
		if os.name == 'nt':
			self.error_icon = ".."+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-illegal')
			self.warning_icon = ".."+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-warning')
		else:
			self.error_icon = "Packages"+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-illegal.png')
			self.warning_icon = "Packages"+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-warning.png')


	def init(self,root):
		pass
		# TODO i suppose it's not needed anymore
		# debounce(TSS.errors, 0, 'errors' + str(id(TSS)), root)
		

	def on_results(self, errors, filename):
		""" this is the default callback from the async process if new errors have been calculated """
		if ST3:
			self.show(errors)
		else:
			sublime.set_timeout(lambda: self.show(errors), 1)

	def show(self, errors):
		try:
			errors = json.loads(errors)
			self.highlight(errors)
			if VIEWS.error_view_available:
				sublime.active_window().run_command('typescript_error_panel_view',{"errors":errors})
		except:
			print('show_errors json error : ',errors)


	def highlight(self, errors):
		""" update hightlights (red underline) in all files """

		self.errors = {}

		# iterate through all open views, to remove all remaining outdated underlinings
		for window in sublime.windows():
			for view in window.views():
				if is_ts(view):
					error_regions = []
					warning_regions = []

					key = fn2k(view.file_name())
					self.errors[key] = {}

					for e in errors:
						if fn2k(e['file']) == key:
							start_line = e['start']['line']
							end_line = e['end']['line']
							left = e['start']['character']
							right = e['end']['character']

							a = view.text_point(start_line-1,left-1)
							b = view.text_point(end_line-1,right-1)


							self.errors[key][(a,b)] = e['text']

							if e['category'] == 'Error': 
								error_regions.append(sublime.Region(a,b))
							else:
								warning_regions.append(sublime.Region(a,b))

					# apply regions, even if empty
					view.add_regions('typescript-error' , error_regions , 'invalid' , self.error_icon, self.underline)
					view.add_regions('typescript-warnings' , warning_regions , 'invalid' , self.warning_icon, self.underline)


	def set_status(self,view):
		error = self._get_error_at(view.sel()[0].begin(),view.file_name())
		if error != None:
			sublime.status_message(error)
		else:
			sublime.status_message('')


	def _get_error_at(self,pos,filename):
		if fn2k(filename) in self.errors:
			for (l, h), e in self.errors[fn2k(filename)].items():
				if pos >= l and pos <= h:
					return e

		return None


# --------------------------------------- INIT -------------------------------------- #

ERRORS = Errors()
