# coding=utf8

import sublime
from ...Utils import Debug, max_calls

class Base(object):
	"""
		This object represents a special view to display T3S information like
		the error list or the outline structure
	"""

	def __init__(self, name, t3sviews):
		self.name = name
		self.t3sviews = t3sviews
		self.is_updating = False # text changes
		self._view_reference = None

	@max_calls()
	def enable(self):
		"""
			searches for open views with the title of this view (eg 'Typescript : Errors List')
			and uses them. If no such view can be found, it creates one and layoutes it to group 1
		"""
		if self.get_view() is None:

			## add next to existing t3s views
			## or create layout if not created yet
			(window, group) = self.t3sviews.get_window_and_group_for_new_views()
			
			view = window.new_file()
			self._set_up_view(view)

			self.t3sviews.layout.add_view(window, view, group)
			self._view_reference = view

		return self._view_reference

	@max_calls()
	def _set_up_view(self, view):
		view.set_name(self.name)
		view.set_scratch(True)
		view.set_read_only(True)
		view.set_syntax_file('Packages/T3S/theme/Typescript.tmLanguage')
		view.settings().set('line_numbers', False)
		view.settings().set('word_wrap', True)
		view.settings().set('extensions',['js'])

	@max_calls()
	def bring_to_top(self, back_to=None):
		Debug('focus', 'bring_to_top: focus view %i' % self._view_reference.id())
		self._view_reference.window().focus_view(self._view_reference)
		if back_to is not None:
			Debug('focus', 'bring_to_top: back_to: focus view %i' % back_to.id())
			back_to.window().focus_view(back_to)

	@max_calls()
	def hide(self):
		""" closes this special T3S view """
		v = self.get_view()
		if v is not None:
			v.close()

	def is_active(self):
		return self.get_view() is not None

	def get_view(self):
		if self._is_view_still_open():
			return self._view_reference
		elif self._search_existing_view():
			return self._view_reference
		return None

	def _is_view_still_open(self):
		if self._view_reference is None:
			return False
		return self._view_reference.is_valid()

	def _search_existing_view(self):
		"""
			returns True if a view with the name of
			this T3S view is open and sets it as reference
		"""
		for w in sublime.windows():
			for v in w.views():
				if v.name() == self.name:
					self._view_reference = v
					self.on_overtook_existing_view()
					return self._is_view_still_open()
		return False

	@max_calls()
	def set_text(self, edit_token, content):
		if not self._is_view_still_open():
			return
		self.is_updating = True
		self._view_reference.set_read_only(False)
		self._view_reference.erase(edit_token, sublime.Region(0, self._view_reference.size()))
		self._view_reference.insert(edit_token, 0, content)
		self._view_reference.set_read_only(True)
		self.is_updating = False

	@max_calls()
	def on_closed(self):
		self.t3sviews.update_layout()
		pass

	@max_calls()
	def on_selection_modified(self):
		if self._is_view_still_open() and not self.is_updating:
			begin = self._view_reference.sel()[0].begin()
			(line, col) = self._view_reference.rowcol(begin)
			self.on_click(line)

	@max_calls()
	def on_click(self, line):
		pass #overwrite

	def on_overtook_existing_view(self):
		pass






















