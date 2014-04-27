# coding=utf8

from .Base import Base

class Compile(Base):

	ts_view = None;

	def __init__(self,name,view):
		super(Compile, self).__init__(name,view)

	def setup(self,ts_view):
		self.ts_view = ts_view

	def on_click(self,line):
		if self.ts_view: 
				if self.ts_view.window():
					self.ts_view.window().focus_view(self.ts_view)