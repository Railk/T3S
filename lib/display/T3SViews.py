# coding=utf8

import sublime
import sublime_plugin
import time

from .Layout import Layout
from .views.Outline import Outline
from .views.Error import Error
from .views.Compile import Compile
from ..Utils import Debug, max_calls

class T3SViews (object):
	""" This class manages the 3 views:
			Error List
			Build File   output
            Outline View """

	# INIT
	def __init__(self):

		self.ERROR = Error(self)
		self.COMPILE = Compile(self)
		self.OUTLINE = Outline(self)
		
		# remembers group and window so we can delete the group if all windows are closed
		self._group = None
		self._window = None
		
		self.layout = Layout()

					
	# HAS VIEWS *
	def has_open_views(self):
		return self.get_an_open_t3sview() is not None

	# GET WINDOW & VIEW GROUP FOR NEW T3S VIEWS *
	def get_window_and_group_for_new_views(self):
		"""
			returns the sublime window and the sublime group in which the first 
			open T3S view is located (or should be inserted)
		"""
		if not self.has_open_views():
			self._window = sublime.active_window()
			self.layout.create(self._window)
			self._group = self._window.num_groups()-1
		else:
			tv = self.get_an_open_t3sview()
			if tv is None:
				return self.get_window_and_group_for_new_views()
			sublime_view = tv.get_view()
			self._window = sublime_view.window()
			(self._group, index) = self._window.get_view_index(sublime_view)
		return (self._window, self._group)

	# GET ANY T3SVIEW *
	def get_an_open_t3sview(self):
		""" returns first T3S view available """
		if self.ERROR.get_view() is not None:
			return self.ERROR
		if self.OUTLINE.get_view() is not None:
			return self.OUTLINE
		if self.COMPILE.get_view() is not None:
			return self.COMPILE
		return None

	# UPDATE LAYOUT *
	def update_layout(self):
		sublime.set_timeout( lambda:self.layout.update(self._window,self._group), 1)

	# FIND T3SVIEW for SUBLIME VIEW*
	def find_t3sview_for_view(self, sublime_view):
		if self._window is None:
			self.get_window_and_group_for_new_views()
		if self.ERROR.is_active() and sublime_view.id() == self.ERROR.get_view().id():
			return self.ERROR
		if self.COMPILE.is_active() and sublime_view.id() == self.COMPILE.get_view().id():
			return self.COMPILE
		if self.OUTLINE.is_active() and sublime_view.id() == self.OUTLINE.get_view().id():
			return self.OUTLINE
		return None

class TypescriptEventListener2(sublime_plugin.EventListener):

	@max_calls(name='T3SViews.on_close')
	def on_close(self, view):
		# Already closed
		v = T3SVIEWS.find_t3sview_for_view(view)
		if v is not None:
			v.on_closed()

	@max_calls(name='T3SViews.on_selection_modified')
	def on_selection_modified(self,view):
		v = T3SVIEWS.find_t3sview_for_view(view)
		if v is not None:
			v.on_selection_modified()


# --------------------------------------- INITIALISATION -------------------------------------- #

T3SVIEWS = T3SViews()
