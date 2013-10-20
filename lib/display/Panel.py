# coding=utf8

from ..Utils import ST3

class Panel(object):

	panel = None		

	def show(self,window):
		self.window = window
		if not self.panel:
			self.panel = self.create_output_panel(self.window,'typescript_output')

	def hide(self):
		self.window.run_command("hide_panel", {"panel": "output.typescript_output"})

	def update(self,output):
		if ST3:
			self.panel.run_command('append', {'characters': output})
		else:
			edit = self.panel.begin_edit()
			self.panel.insert(edit, self.panel.size(), output)
			self.panel.end_edit(edit)
			
		self.window.run_command("show_panel", {"panel": "output.typescript_output"})

	def clear(self,window):
		self.window = window
		self.panel = self.create_output_panel(self.window,'typescript_output')

	def create_output_panel(self,window,name):
		if ST3: return window.create_output_panel(name)
		else: return window.get_output_panel(name)

# --------------------------------------- INITIALISATION -------------------------------------- #

PANEL = Panel()		