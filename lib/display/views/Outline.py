# coding=utf8

import sublime
from .Base import Base

class Outline(Base):

	regions = None

	def __init__(self,name,view):
		super(Outline, self).__init__(name,view)

	def setup(self,ts_view,regions):
		self.regions = regions
		self.ts_view = ts_view

	def on_click(self,line):
		if not self.regions: return
		if line in self.regions:
			draw = sublime.DRAW_NO_FILL if int(sublime.version()) >= 3000 else sublime.DRAW_OUTLINED
			self.ts_view.show(self.regions[line])
			self.ts_view.add_regions('typescript-definition', [self.regions[line]], 'comment', 'dot', draw)