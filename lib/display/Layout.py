# coding=utf8

import sublime
from ..Utils import ST3


class Layout(object):

	def __init__(self):
		super(Layout, self).__init__()


	# GET LAYOUT
	def get_layout(self,window):
		layout = window.get_layout()
		cells = layout["cells"]
		rows = layout["rows"]
		cols = layout["cols"]
		return rows, cols, cells

	# SET LAYOUT
	def set_layout(self, window, layout, delete=False):
		if delete:
			if ST3: window.set_layout(layout)
			else: sublime.set_timeout(lambda:window.set_layout(layout),1)
		else:
			window.set_layout(layout)

		active_group = window.active_group()
		num_groups = len(layout['cells'])
		window.focus_group(min(active_group, num_groups-1))


	# ADD VIEW
	def add_view(self,window,view,group):
		window.focus_group(group)
		window.set_view_index(view, window.active_group(), 0)


	# CREATE PANE
	def create(self,window):
		rows, cols, cells = self.get_layout(window)

		MAXROWS = len(rows)-1
		MAXCOLS = len(cols)-1

		cols[MAXCOLS] = cols[MAXCOLS-1]+(cols[MAXCOLS]-cols[MAXCOLS-1])*0.65
		cols.append(1.0)
		cells.append([MAXCOLS,0,MAXCOLS+1,MAXROWS])

		layout = {"cols": cols, "rows": rows, "cells": cells}
		self.set_layout(window, layout)


	# DESTROY CURRENT PANE
	def delete(self,window):
		rows, cols, cells = self.get_layout(window)
		if len(cells)<2: return

		cols.pop(-1)
		MAXCOLS = len(cols)-1
		cols[MAXCOLS] = 1.0
		del cells[len(cells)-1]

		layout = {"cols": cols, "rows": rows, "cells": cells}
		self.set_layout(window, layout, True)