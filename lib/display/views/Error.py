# coding=utf8

import sublime
import time
import re

from .Base import Base
from ...Utils import Debug, max_calls, ST3

class Error(Base):


	def __init__(self, t3sviews):
		super(Error, self).__init__('Typescript : Errors List', t3sviews)
		self.files = {}
		self.points = {}
		self.text = ""

	# enable
	def enable(self, edit_token=None):
		super(Error, self).enable()
		if edit_token is not None:
			# set text if already known
			super(Error, self).set_text(edit_token, self.text)
			self.update_message()

	# SET TEXT
	def set_text(self, edit_token, errors):
		"""
			This function takes the tss.js errors structure instead of a string.
		"""
		# this will process the errors, even if the view is closed
		if type(errors) == list:
			self._tssjs_2_errorview_format(errors)
		else:
			self.text = "\n\n\n%s" % errors
			self.points = {}
			self.files = {}
		super(Error, self).set_text(edit_token, self.text)

	# ON CLICK
	@max_calls(name='Error.on_click')
	def on_click(self,line):
		if line in self.points and line in self.files:
			view = sublime.active_window().open_file(self.files[line])			
			self._focus_error_in_view(view, self.points[line])

	def _focus_error_in_view(self, view, point):
		if view.is_loading():
			sublime.set_timeout(lambda: self._focus_error_in_view(view, point), 100)
			return
		else:
			a = view.text_point(*point[0])
			b = view.text_point(*point[1]) 
			region = sublime.Region(a,b)

			Debug('focus', 'Error click -> _focus_error_in_view %i, %s' % (view.id(), view.file_name()))
			view.window().focus_view(view)

			Debug('focus', "show_at_center, Region @pos %i, (%s -> %s)" % (region.begin(), point[0], point[1]))
			view.show_at_center(region)

			draw = sublime.DRAW_NO_FILL if ST3 else sublime.DRAW_OUTLINED
			view.add_regions('typescript-error-hint', [region], 'invalid', 'dot')

			#sel = view.sel()
			#sel.clear()
			#sel.add(sublime.Region(a,a))

	def _tssjs_2_errorview_format(self, errors):
		"""
			Takes the de-jsoned output of the tss.js error command and creates the content for the error view.
			It also creates a relation between each line in the error view and the file and position of the error.
			Results are available in self.files, self.points and self.text
		"""
		self.files = {}
		self.points = {}

		text = [self.create_message()[1]]
		previous_file = ''
		line = 0

		for e in errors:
			filename = e['file'].split('/')[-1]
			if previous_file != filename:
				text.append("\n\nOn File : %s \n" % filename)
				line += 3
				previous_file = filename

			text.append("\n%i >" % e['start']['line'])
			text.append(re.sub(r'^.*?:\s*', '', e['text'].replace('\r','')))
			line += 1

			a = (e['start']['line']-1, e['start']['character']-1)
			b = (e['end']['line']-1, e['end']['character']-1)
			self.points[line] = (a,b)
			self.files[line] = e['file']


		if len(errors) == 0: 
			text.append("\n\nno errors")
		
		text.append('\n')
		self.text = ''.join(text)

	def on_overtook_existing_view(self):
		""" empty view on plugin start """
		self._view_reference.run_command("typescript_error_panel_set_text", {"errors": []} )
		pass


	# MANAGING ERROR CALCULATION STATUS MESSAGES
	last_bounce_time = 0

	calculation_is_running = False
	execution_started_time = 0
	finished_time = 0
	last_execution_duration = 0

	def on_calculation_initiated(self):
		Debug('errorpanel', "Calc init")
		self.last_bounce_time = time.time()
		self.update_message()

	def on_calculation_replaced(self):
		Debug('errorpanel', "Calc replaced")
		self.last_bounce_time = time.time()
		self.update_message()

	def on_calculation_executing(self):
		Debug('errorpanel', "Calc executing")
		self.execution_started_time = time.time()
		self.calculation_is_running = True
		self.update_message()

	def on_calculation_finished(self):
		Debug('errorpanel', "Calc finished")
		self.finished_time = time.time()
		self.last_execution_duration = self.finished_time - self.execution_started_time
		self.calculation_is_running = False
		self.update_message()

	def is_unstarted_calculation_pending(self):
		return self.last_bounce_time > self.execution_started_time

	@max_calls()
	def update_message(self):
		""" update the message displayed on top of the error view """
		need_recall, msg = self.create_message()
		if need_recall:
			sublime.set_timeout(lambda: self.update_message(), 1000)
		## calls set_error_calculation_status_message() with an edit_token
		if self._is_view_still_open():
			Debug('errorpanel', "Error view: %s %a" % (self._view_reference.name(), self._view_reference.file_name()))
			self._view_reference.run_command('typescript_set_error_calculation_status_message', {"message": msg}) 

	def create_message(self):
		""" returns (need_recall, msg) """
		need_recall = False # only issue timeout to this function once

		msg = "//   "
		if self.last_execution_duration > 0: # there was a previous calculation

			# /"""""""""""""\
			msg += "/".ljust(int(self.last_execution_duration) + 1, "\"") + "\\"

			# indicate 'oldness' of calculation: (5s ago)
			oldness = int(time.time() - self.finished_time)
			if oldness < 10:
				msg += " (%is ago) " % oldness
				need_recall = True
			else:
				msg += " (long ago) "

		if self.calculation_is_running: # calculating: /""""""""
			calculation_time = time.time() - self.execution_started_time
			msg += "/".ljust(int(calculation_time) + 1, "\"")
			need_recall = True
			
		# after this calculation another calculation will be started: ... 
		if self.is_unstarted_calculation_pending():
			msg += " ..."
		return (need_recall, msg)

	def set_error_calculation_status_message(self, edit_token, message):
		if not self._is_view_still_open():
			return
		Debug('errorpanel+', "message: %s" % (message))
		self.is_updating = True
		self._view_reference.set_read_only(False)
		self._view_reference.replace(edit_token, self._view_reference.full_line(0), message + "\n")
		self._view_reference.set_read_only(True)
		self.is_updating = False








