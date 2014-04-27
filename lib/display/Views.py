# coding=utf8

import sublime

from .Layout import Layout
from .views.Outline import Outline
from .views.Error import Error
from .views.Compile import Compile


class Views (object):

	group = None
	window = None
	has_error = False
	inited = False
	layout = Layout()
	views ={}
	liste = [
		('error','Typescript : Errors List'),
		('compile','Typescript : Built File'),
		('outline','Typescript : Outline View')
	]
			
	# INIT
	def init(self):
		if self.inited: return
		self.inited = True

		windows = sublime.windows()
		for window in windows:
			for line in self.liste:
				self.find_open_view(window,*line)

	# UPDATE
	def update(self):
		if self.is_open_view('Typescript : Outline View'): sublime.active_window().run_command('typescript_structure')
		if self.is_open_view('Typescript : Errors List'): sublime.active_window().run_command('typescript_error_panel')
		if self.views and self.window:
			if self.layout.update(self.window,self.group):
				window = sublime.active_window()
				(self.window,self.group) = self.get_view_group(window)


	# HAS VIEWS
	def has_view(self):
		if not self.views: return False
		else: return True


	# IS VIEW
	def is_view(self,name):
		if 	name == 'Typescript : Errors List' or name == 'Typescript : Built File' or name == 'Typescript : Outline View': return True
		return False


	# IS OPEN VIEW
	def is_open_view(self,name):
		return name in self.views


	# CREATE VIEW
	def create_view(self,ts_view,kind,edit,name,content):
		window = sublime.active_window()
		view = None

		if not self.views: self.layout.create(window)

		if name in self.views:
			view = self.views[name]
		else:
			view = self.create_view_kind(kind,name,None)
			(self.window,self.group) = self.get_view_group(window)
			self.layout.add_view(self.window,view.view,self.group)
			self.views[name] = view
		
		view.update(edit,content)
		window.focus_view(ts_view)
		return view


	# GET VIEW GROUP
	def get_view_group(self,window):
		if not self.views:
			return (window,window.num_groups()-1)
		else:
			for view in self.views:
				view = self.views[view].view
				break

			window = view.window()
			(group,index) = window.get_view_index(view)
			return (window,group)


	# VIEW CONTENT CLICK
	def on_view(self,view):
		name = view.name()
		if name in self.views:
			(line, col) = view.rowcol(view.sel()[0].begin())
			self.views[name].on_click(line)


	# DELETE VIEW
	def delete_view(self,name):
		if name in self.views:
			if name == 'Typescript : Errors List': self.has_error = False
			del self.views[name]

		if not self.views:
			sublime.set_timeout(lambda:self.layout.update(self.window,self.group),1)


	# FIND OPEN VIEW
	def find_open_view(self,window,kind,name):
		views = window.views()
		for view in views:
			if view.name() == name:
				self.views[name] = self.create_view_kind(kind,name,view)


	# CREATE VIEW KIND
	def create_view_kind(self,kind,name,view):
		if kind == 'outline': return Outline(name,view)
		elif kind == 'error': return Error(name,view)
		elif kind == 'compile': return Compile(name,view)



# --------------------------------------- INITIALISATION -------------------------------------- #

VIEWS = Views()