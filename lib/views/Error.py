# coding=utf8

import sublime
from .Base import Base

class Error(Base):

	points = None

	def __init__(self,name,view):
		super(Error, self).__init__(name,view)

	def setup(self,files,points):
		self.files =  files
		self.points = points

	def on_click(self,line):
		if not self.points: return
		if line in self.points:	
			view = sublime.active_window().open_file(self.files[line])
			self.open_view(view,*self.points[line])
		

	def open_view(self,view,begin,end):
		if view.is_loading():
			sublime.set_timeout(lambda: self.open_view(view,region), 100)
			return
		else:
			a = view.text_point(*begin)
			b = view.text_point(*end) 
			region = sublime.Region(a,b)
			
			sublime.active_window().focus_view(view)
			view.show(region)