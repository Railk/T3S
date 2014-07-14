# coding=utf8

from threading import Thread

import sublime
import os
import json

from ..Tss import TSS
from ..Utils import dirname, fn2k, is_ts, max_calls

# --------------------------------------- ERRORS -------------------------------------- #

class ErrorsHighlighter(object):

	errors = {}

	underline = sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_EMPTY_AS_OVERWRITE

	def __init__(self):
		if os.name == 'nt':
			self.error_icon = ".."+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-illegal')
			self.warning_icon = ".."+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-warning')
		else:
			self.error_icon = "Packages"+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-illegal.png')
			self.warning_icon = "Packages"+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-warning.png')



	@max_calls(name='Errors.highlight')
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

							a = view.text_point(e['start']['line']-1, e['start']['character']-1)
							b = view.text_point(e['end']['line']-1, e['end']['character']-1)

							self.errors[key][(a,b)] = e['text']

							if e['category'] == 'Error': 
								error_regions.append(sublime.Region(a,b))
							else:
								warning_regions.append(sublime.Region(a,b))

					# apply regions, even if empty (that will remove every highlight in that file)
					view.add_regions('typescript-error' , error_regions , 'invalid' , self.error_icon, self.underline)
					view.add_regions('typescript-warnings' , warning_regions , 'invalid' , self.warning_icon, self.underline)


	previously_error_under_cursor = False

	@max_calls(name='ErrorHighlighter.display_error_in_status_if_cursor')
	def display_error_in_status_if_cursor(self,view):
		"""
			Displays the error message in the sublime status 
			line if the cursor is above an error (in source code).
			For the click on the error list, see T3SVIEWS.ERROR.on_click()
		"""
		error = self._get_error_at(view.sel()[0].begin(),view.file_name())
		if error is not None:
			sublime.status_message(error)
			self.previously_error_under_cursor = True
		elif self.previously_error_under_cursor: # only clear once
			sublime.status_message('')
			self.previously_error_under_cursor = False


	def _get_error_at(self,pos,filename):
		if fn2k(filename) in self.errors:
			for (l, h), e in self.errors[fn2k(filename)].items():
				if pos >= l and pos <= h:
					return e

		return None




# --------------------------------------- INIT -------------------------------------- #

ERRORSHIGHLIGHTER = ErrorsHighlighter()
