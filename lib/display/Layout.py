# coding=utf8
# delete code taken from sublime origami : https://github.com/SublimeText/Origami

import sublime
from ..Utils import ST3

XMIN, YMIN, XMAX, YMAX = list(range(4))

class Layout(object):

	# CONSTRUCTEUR
	def __init__(self):
		super(Layout, self).__init__()


	# UPDATE
	def update(self,window,group):
		views = window.views_in_group(group)
		if len(views) == 0: 
			self.delete(window,group)
			return True

		return False


	# GET LAYOUT
	def get_layout(self,window):
		layout = window.get_layout()
		if not layout: return

		cells = layout["cells"]
		rows = layout["rows"]
		cols = layout["cols"]
		return rows, cols, cells


	# SET LAYOUT
	def set_layout(self,window,layout,delete=False):
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
		window.set_view_index(view, group, 0)


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


	# DELETE
	def delete(self,window,group):
		if not self.get_layout(window): return
		rows, cols, cells = self.get_layout(window)

		current = cells[group]
		choices = {}
		choices["up"] = self.adjacent_cell(window,"up",group)
		choices["right"] = self.adjacent_cell(window,"right",group)
		choices["down"] = self.adjacent_cell(window,"down",group)
		choices["left"] = self.adjacent_cell(window,"left",group)
		
		target_dir = None
		for dir,c in choices.items():
			if not c:
					continue
			if dir in ["up", "down"]:
					if c[XMIN] == current[XMIN] and c[XMAX] == current[XMAX]:
							target_dir = dir
			elif dir in ["left", "right"]:
					if c[YMIN] == current[YMIN] and c[YMAX] == current[YMAX]:
							target_dir = dir

		if not target_dir: return

		
		direction = self.opposite_direction(target_dir)
		current_group = window.active_group()
		cell_to_remove = cells[group]
		
		if cell_to_remove:
			active_view = window.active_view()
			group_to_remove = cells.index(cell_to_remove)
			dupe_views = self.duplicated_views(window,current_group,group_to_remove)
			for d in dupe_views:
				window.focus_view(d)
				window.run_command('close')
			if active_view:
				window.focus_view(active_view)
			
			cells.remove(cell_to_remove)
			if direction == "up":
				rows.pop(cell_to_remove[YMAX])
				adjacent_cells = self.cells_adjacent_to_cell_in_direction(cells, cell_to_remove, "down")
				for cell in adjacent_cells:
						cells[cells.index(cell)][YMIN] = cell_to_remove[YMIN]
				cells = self.pull_up_cells_after(cells, cell_to_remove[YMAX])
			elif direction == "right":
				cols.pop(cell_to_remove[XMIN])
				adjacent_cells = self.cells_adjacent_to_cell_in_direction(cells, cell_to_remove, "left")
				for cell in adjacent_cells:
						cells[cells.index(cell)][XMAX] = cell_to_remove[XMAX]
				cells = self.pull_left_cells_after(cells, cell_to_remove[XMIN])
			elif direction == "down":
				rows.pop(cell_to_remove[YMIN])
				adjacent_cells = self.cells_adjacent_to_cell_in_direction(cells, cell_to_remove, "up")
				for cell in adjacent_cells:
						cells[cells.index(cell)][YMAX] = cell_to_remove[YMAX]
				cells = self.pull_up_cells_after(cells, cell_to_remove[YMIN])
			elif direction == "left":
				cols.pop(cell_to_remove[XMAX])
				adjacent_cells = self.cells_adjacent_to_cell_in_direction(cells, cell_to_remove, "right")
				for cell in adjacent_cells:
						cells[cells.index(cell)][XMIN] = cell_to_remove[XMIN]
				cells = self.pull_left_cells_after(cells, cell_to_remove[XMAX])

			layout = {"cols": cols, "rows": rows, "cells": cells}
			self.set_layout(window, layout, True)


	def adjacent_cell(self,window,direction,group):
		cells = window.get_layout()['cells']
		current_cell = cells[group]
		adjacent_cells = self.cells_adjacent_to_cell_in_direction(cells,current_cell,direction)
		rows, cols, _ = self.get_layout(window)
		
		if direction in ["left", "right"]:
				MIN, MAX, fields = YMIN, YMAX, rows
		else: #up or down
				MIN, MAX, fields = XMIN, XMAX, cols
		
		cell_overlap = []
		for cell in adjacent_cells:
				start = max(fields[cell[MIN]], fields[current_cell[MIN]])
				end = min(fields[cell[MAX]], fields[current_cell[MAX]])
				overlap = (end - start)
				cell_overlap.append(overlap)
		
		if len(cell_overlap) != 0:
				cell_index = cell_overlap.index(max(cell_overlap))
				return adjacent_cells[cell_index]
		return None


	def duplicated_views(self,window,original_group,duplicating_group):
		original_views = window.views_in_group(original_group)
		original_buffers = [v.buffer_id() for v in original_views]
		potential_dupe_views = window.views_in_group(duplicating_group)
		dupe_views = []
		for pd in potential_dupe_views:
				if pd.buffer_id() in original_buffers:
						dupe_views.append(pd)
		return dupe_views


	def cells_adjacent_to_cell_in_direction(self,cells,cell,direction):
		fn = None
		if direction == "up": fn = lambda orig, check: orig[YMIN] == check[YMAX]
		elif direction == "right": fn = lambda orig, check: orig[XMAX] == check[XMIN]
		elif direction == "down": fn = lambda orig, check: orig[YMAX] == check[YMIN]
		elif direction == "left": fn = lambda orig, check: orig[XMIN] == check[XMAX]
		if fn: return [c for c in cells if fn(cell, c)]
		return None


	def opposite_direction(self,direction):
		opposites = {"up":"down", "right":"left", "down":"up", "left":"right"}
		return opposites[direction]


	def pull_left_cells_after(self,cells,threshold):
		return [[self.decrement_if_greater(x0, threshold),y0,self.decrement_if_greater(x1, threshold),y1] for (x0,y0,x1,y1) in cells]


	def decrement_if_greater(self,x,threshold):
		if x > threshold: return x-1
		return x