# coding=utf8

from threading import Thread

import sublime
import os
import json

from .View import VIEW
from ..Tss import TSS
from ..Utils import dirname, debounce, get_file_infos, ST3

# --------------------------------------- ERRORS -------------------------------------- #

class Errors(object):

	errors = {}
	errors_reader = {}

	def __init__(self):
		if os.name == 'nt':
			self.error_icon = ".."+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-illegal')
			self.warning_icon = ".."+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-warning')
		else:
			self.error_icon = "Packages"+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-illegal.png')
			self.warning_icon = "Packages"+os.path.join(dirname.split('Packages')[1], 'icons', 'bright-warning.png')


	def init(self,root,queue):
		reader = ErrorsReader(queue)
		reader.daemon = True
		reader.start()

		self.errors_reader[root] = reader 
		debounce(TSS.errors, 0, 'errors' + str(id(TSS)), *get_file_infos(sublime.active_window().active_view()))


	def remove(self,root):
		if root in self.errors_reader:
			del self.errors_reader[root]
		

	def show(self,view,errors):
		try:
			errors = json.loads(errors)
			self.highlight(view,errors)
			if VIEW.has_error: sublime.active_window().run_command('typescript_error_panel_view',{"errors":errors})
		except:
			print('show_errors json error : ',errors)


	def highlight(self,view,errors) :
		error_regions = []
		warning_regions = []
		filename = view.file_name()

		self.errors[filename] = {}
		for e in errors :
			if e['file'].replace('/',os.sep).lower() == filename.lower():
				start_line = e['start']['line']
				end_line = e['end']['line']
				left = e['start']['character']
				right = e['end']['character']

				a = view.text_point(start_line-1,left-1)
				b = view.text_point(end_line-1,right-1)
				self.errors[filename][(a,b)] = e['text']

				if e['category'] == 'Error': 
					error_regions.append(sublime.Region(a,b))
				else:
					warning_regions.append(sublime.Region(a,b))

		view.add_regions('typescript-error' , error_regions , 'invalid' , self.error_icon)
		view.add_regions('typescript-warnings' , warning_regions , 'invalid' , self.warning_icon)


	def set_status(self,view):
		error = self._get_error_at(view.sel()[0].begin(),view.file_name())
		if error != None:
			sublime.status_message(error)
		else:
			sublime.status_message('')


	def _get_error_at(self,pos,filename):
		if filename in self.errors:
			for (l, h), error in self.errors[filename].items():
				if pos >= l and pos <= h:
					return error

		return None

# ----------------------------------- ERRORS READER --------------------------------- #

class ErrorsReader(Thread):

	def __init__(self,queue):
		self.queue = queue
		Thread.__init__(self)

	def run(self):
		for line in iter(self.queue.get, None):
			if ST3: ERRORS.show(sublime.active_window().active_view(),line)
			else: sublime.set_timeout(lambda: ERRORS.show(sublime.active_window().active_view(),line), 1)


# --------------------------------------- INIT -------------------------------------- #

ERRORS = Errors()