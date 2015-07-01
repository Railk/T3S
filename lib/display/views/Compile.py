# coding=utf8

from .Base import Base

class Compile(Base):

	ts_view = None;

	def __init__(self, t3sviews):
		super(Compile, self).__init__('Typescript : Built File', t3sviews)

	def setup(self,ts_view):
		self.ts_view = ts_view

	def on_click(self,line):
		if self.ts_view: 
			if self.ts_view.window():
				self.ts_view.window().focus_view(self.ts_view)
