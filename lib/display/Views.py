# coding=utf8

import sublime
import time

from .Layout import Layout
from .views.Outline import Outline
from .views.Error import Error
from .views.Compile import Compile
from ..Utils import Debug

class Views (object):
	""" This class manages the 3 views:
			Error List
			Build File   output
            Outline View """

	group = None
	window = None
	error_view_available = False # can be true even if not open, signals activation of show_error mode
	inited = False
	layout = Layout()
	open_views = {} # keys are the view names,eg 'Typescript : Errors List'
	viewnames = {
		'error': 'Typescript : Errors List',
		'compile': 'Typescript : Built File',
		'outline' :'Typescript : Outline View'
	}
			
	# INIT
	def init(self):
		if self.inited: return
		self.inited = True

		self.find_open_views()


	# UPDATE
	def update(self):
		if self.is_open_view(_type='outline'): sublime.active_window().run_command('typescript_structure')
		if self.is_open_view(_type='error'): sublime.active_window().run_command('typescript_error_panel')
		if self.has_open_views() and self.window:
			if self.layout.update(self.window,self.group):
				window = sublime.active_window()
				(self.window,self.group) = self.get_view_group(window)


	# HAS VIEWS
	def has_open_views(self):
		return len(self.open_views) > 0


	# IS VIEW
	def is_view(self, name):
		return name in self.viewnames.values()


	# IS OPEN VIEW
	def is_open_view(self, _type=None, name=None):
		""" checks if view is open. use with name= or _type= """
		if _type != None:
			return self.viewnames[_type] in self.open_views
		if name != None:
			return name in self.open_views
		raise ValueError

	# IS OPEN VIEW
	def get_view(self, _type=None, name=None):
		""" returns view if view is open. use with name= or _type= """
		if _type != None:
			return self.open_views[self.viewnames[_type]]
		if name != None:
			return self.open_views[name]
		raise ValueError


	# CREATE VIEW
	def create_or_open_view(self, ts_view, _type, edit_token, content):
		window = sublime.active_window()
		view = None

		if not self.has_open_views():
			self.layout.create(window)

		if self.is_open_view(_type=_type):
			view = self.get_view(_type=_type)
		else:
			view = self.create_view_class(_type) # new view (sublime as well as T3S)
			(self.window,self.group) = self.get_view_group(window)
			self.layout.add_view(self.window, view.view, self.group)
			self.open_views[self.viewnames[_type]] = view
		
		view.update(edit_token, content)
		window.focus_view(ts_view)
		return view


	# GET VIEW GROUP
	def get_view_group(self,window):
		""" returns the sublime window and the sublime group in which the first open T3S view is located (or should be inserted) """
		if not self.has_open_views():
			return (window,window.num_groups()-1)
		else:
			sublime_view = self.get_a_view().view
			window = sublime_view.window()
			(group, index) = window.get_view_index(sublime_view)
			return (window, group)


	def get_a_view(self):
		""" returns first T3S view available """
		for name in self.open_views:
			return self.open_views[name]


	# VIEW CONTENT CLICK
	def on_view_clicked(self, sublime_view):
		name = sublime_view.name()
		if self.is_open_view(name=name):
			(line, col) = sublime_view.rowcol(sublime_view.sel()[0].begin())
			self.open_views[name].on_click(line)


	# DELETE VIEW (from on_close view)
	def delete_view(self, name):
		if name in self.open_views:
			if name == self.viewnames['error']:
				self.error_view_available = False
			del self.open_views[name]

		if not self.open_views and self.window:
			sublime.set_timeout( lambda:self.layout.update(self.window,self.group), 1)


	# FIND OPEN VIEW
	def find_open_views(self):
		""" searches for already open special views and overtake them"""
		for window in sublime.windows():
			for view in window.views():
				for _type, name in self.viewnames.items():
					if view.name() == name:
						self.open_views[name] = self.create_view_class(_type, view)


	# CREATE VIEW of _type
	def create_view_class(self, _type, recycle_view=None):
		if _type == 'outline': return Outline(self.viewnames[_type], recycle_view)
		elif _type == 'error':
			self.error_view_available = True # enabled from earlier (sublime restart)
			return Error(self.viewnames[_type], recycle_view)
		elif _type == 'compile': return Compile(self.viewnames[_type], recycle_view)


	# MANAGING ERROR CALCULATION STATUS MESSAGES
	last_bounce_time = 0

	is_executing = False
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
		self.is_executing = True
		self.update_message()

	def on_calculation_finished(self):
		Debug('errorpanel', "Calc finished")
		self.finished_time = time.time()
		self.last_execution_duration = self.finished_time - self.execution_started_time
		self.is_executing = False
		self.update_message()

	def is_unstarted_calculation_pending(self):
		return self.last_bounce_time > self.execution_started_time

	def update_message(self):
		msg = "//   "
		if self.last_execution_duration > 0: # there was a previous calculation
			msg += "/".ljust(int(self.last_execution_duration) + 1, "\"") + "\\"
			# indicate 'oldness' of calculation
			oldness = int(time.time() - self.finished_time)
			if oldness < 10:
				msg += " (%is ago) " % oldness
			else:
				msg += " (long ago) "

		if self.is_executing: # calculating
			calculation_time = time.time() - self.execution_started_time
			msg += "/".ljust(int(calculation_time) + 1, "\"")
		#else:	# calculation finished

		if self.is_unstarted_calculation_pending():
			msg += " ..."

		sublime.active_window().run_command('typescript_error_calculation_status',
			{"message": msg})

		#if self.is_executing:
		sublime.set_timeout(lambda: self.update_message(), 1000)


# --------------------------------------- INITIALISATION -------------------------------------- #

VIEWS = Views()
