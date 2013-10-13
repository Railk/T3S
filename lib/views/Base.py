# coding=utf8

import sublime

class Base(object):

	def __init__(self,name,view):
		self.name = name
		self.view = sublime.active_window().new_file() if view == None else view
		self.view.set_name(name)
		self.view.set_scratch(True)
		self.view.set_read_only(True)
		self.view.set_syntax_file('Packages/T3S/theme/Typescript.tmLanguage')
		self.view.settings().set('line_numbers', False)
		self.view.settings().set('word_wrap', True)
		self.view.settings().set('extensions',['js'])

	def update(self,edit,content):
		self.view.set_read_only(False)
		self.view.erase(edit, sublime.Region(0, self.view.size()))
		self.view.insert(edit,0,content)
		self.view.set_read_only(True)

	def set_focus(self):
		sublime.active_window().focus_view(self.view)