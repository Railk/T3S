# coding=utf8

import sublime
import sublime_plugin
import os
import re

from .Utils import get_data, get_root, debounce, ST3
from .Compiler import Compiler
from .Refactor import Refactor
from .View import VIEW
from .Tss import TSS
from .Message import MESSAGE


# AUTO COMPLETION
class TypescriptComplete(sublime_plugin.TextCommand):

	def run(self, edit, characters):
		for region in self.view.sel():
			self.view.insert(edit, region.end(), characters)

		TSS.update(self.view)
		TSS.get_interface_completion(characters != '.' and self.view.substr(self.view.sel()[0].begin()-1) == ':')
		TSS.get_method_completion(characters != '.' and self.view.substr(self.view.sel()[0].begin()-1) == '(')

		self.view.run_command('auto_complete',{
			'disable_auto_insert': True,
			'api_completions_only': True,
			'next_completion_if_showing': True
		})


# RELOAD PROJECT
class TypescriptReloadProject(sublime_plugin.TextCommand):

	def run(self, edit):
		sublime.status_message('reloading project')
		TSS.reload(self.view)


# SHOW INFOS
class TypescriptType(sublime_plugin.TextCommand):

	def run(self, edit):
		if TSS.get_process(self.view) == None:
			MESSAGE.show('You must wait for the initialisation to finish')
			return

		if not ST3: return
		
		pos = self.view.sel()[0].begin()
		(line, col) = self.view.rowcol(pos)
		types = TSS.type(self.view,line,col)

		if types == None: return
		if 'kind' not in types: return

		kind = TSS.get_prefix(types['kind'])
		if types['docComment'] != '':
			liste = types['docComment'].split('\n')+[kind+' '+types['fullSymbolName']+' '+types['type']]
		else :
			liste = [kind+' '+types['fullSymbolName']+' '+types['type']]

		self.view.show_popup_menu(liste,None)


# GO TO DEFINITION
class TypescriptDefinition(sublime_plugin.TextCommand):

	def run(self, edit):
		if TSS.get_process(self.view) == None:
			MESSAGE.show('You must wait for the initialisation to finish')
			return

		pos = self.view.sel()[0].begin()
		(line, col) = self.view.rowcol(pos)
		definition = TSS.definition(self.view,line,col)

		if definition == None: return
		if 'file' not in definition: return

		view = sublime.active_window().open_file(definition['file'])
		self.open_view(view,definition)

	def open_view(self,view,definition):
		if view.is_loading():
			sublime.set_timeout(lambda: self.open_view(view,definition), 100)
			return
		else:
			start_line = definition['min']['line']
			end_line = definition['lim']['line']
			left = definition['min']['character']
			right = definition['lim']['character']

			a = view.text_point(start_line-1,left-1)
			b = view.text_point(end_line-1,right-1)
			region = sublime.Region(a,b)

			sublime.active_window().focus_view(view)
			view.show_at_center(region)

			draw = sublime.DRAW_NO_FILL if ST3 else sublime.DRAW_OUTLINED
			view.add_regions('typescript-definition', [region], 'comment', 'dot', draw)


# BASIC REFACTORING
class TypescriptReferences(sublime_plugin.TextCommand):

	def run(self, edit):
		if TSS.get_process(self.view) == None:
			MESSAGE.show('You must wait for the initialisation to finish')
			return

		pos = self.view.sel()[0].begin()
		(line, col) = self.view.rowcol(pos)
		self.refs = refs = TSS.references(self.view,line,col)
		self.window = sublime.active_window()

		if refs == None: return

		refactor_member = ""
		try :
			for ref in refs:
				if ref['file'].replace('/',os.sep).lower() == self.view.file_name().lower():
					refactor_member = self.view.substr(self.get_region(self.view,ref['min'],ref['lim']))
			
			self.window.show_input_panel('Refactoring',refactor_member,self.on_done,None,None)
		except (Exception) as ref:
			sublime.status_message("error panel : plugin not yet intialize please retry after initialisation")

	def get_region(self,view,min,lim):
		start_line = min['line']
		end_line = lim['line']
		left = min['character']
		right = lim['character']

		a = view.text_point(start_line-1,left-1)
		b = view.text_point(end_line-1,right-1)
		return sublime.Region(a,b)

	def on_done(self,name):
		refactor = Refactor(self.window,get_root(),name,self.refs)
		refactor.daemon = True
		refactor.start()


# NAVIGATE IN FILE
class TypescriptStructure(sublime_plugin.TextCommand):

	def run(self, edit):
		if TSS.get_process(self.view) == None:
			MESSAGE.show('You must wait for the initialisation to finish')
			return

		ts_view = self.view
		regions = {}
		members = TSS.structure(ts_view)

		try:
			characters = ""
			lines = 0
			for member in members:
				start_line = member['min']['line']
				end_line = member['lim']['line']
				left = member['min']['character']
				right = member['lim']['character']

				a = ts_view.text_point(start_line-1,left-1)
				b = ts_view.text_point(end_line-1,right-1)
				region = sublime.Region(a,b)
				kind = TSS.get_prefix(member['loc']['kind'])
				container_kind = TSS.get_prefix(member['loc']['containerKind'])

				if member['loc']['kind'] != 'class' and member['loc']['kind'] != 'interface':
					line = kind+' '+member['loc']['kindModifiers']+' '+member['loc']['kind']+' '+member['loc']['name']
					characters = characters+'\n\t'+line.strip()
					lines += 1
					regions[lines] = region
				else:
					line = container_kind+' '+member['loc']['kindModifiers']+' '+member['loc']['kind']+' '+member['loc']['name']+' {'
					if characters == "":
						characters = '\n'+characters+line.strip()+'\n'
						lines+=1
						regions[lines] = region
						lines+=1
					else:
						characters = characters+'\n\n}'+'\n\n'+line.strip()+'\n'
						lines+=4
						regions[lines] = region
						lines+=1


			if characters != "": characters += '\n\n}'
			view = VIEW.create_view(ts_view,'outline',edit,'Typescript : Outline View',characters)
			view.setup(ts_view,regions)

		except (Exception) as e:
			e = str(e)
			sublime.status_message("File navigation : "+e)
			print("File navigation : "+e)


# OPEN ERROR PANEL
class TypescriptErrorPanel(sublime_plugin.TextCommand):

	def run(self, edit):
		if TSS.get_process(self.view) == None:
			MESSAGE.show('You must wait for the initialisation to finish')
			return

		VIEW.has_error = True
		debounce(TSS.errors_async, 0.3, 'errors' + str(id(TSS)), self.view)


class TypescriptErrorPanelView(sublime_plugin.TextCommand):

	def run(self, edit, errors):
		self.edit = edit

		try:
			if len(errors) == 0: 
				VIEW.create_view(self.view,'error',self.edit,'Typescript : Errors List','no errors')
			else:
				self.open_panel(errors)
		except (Exception) as e:
			e = str(e)
			sublime.status_message("Error panel : "+e)
			print("Error panel: "+e)


	def open_panel(self,errors):
		files = {}
		points = {}

		characters = ''
		previous_file = ''
		lines = 0
		for e in errors:
			segments = e['file'].split('/')
			last = len(segments)-1
			filename = segments[last]

			start_line = e['start']['line']
			end_line = e['end']['line']
			left = e['start']['character']
			right = e['end']['character']

			a = (start_line-1,left-1)
			b = (end_line-1,right-1)

			if previous_file != filename:
				if characters == "":
					characters += "On File : " + filename+'\n'
					lines +=2
				else:
					characters += "\n\nOn File : " + filename+'\n'
					lines +=3

			characters += '\n\t'+"On Line " + str(start_line) +' : '+re.sub(r'^.*?:\s*', '', e['text'])
			points[lines] = (a,b)
			files[lines] = e['file']

			lines+=1
			previous_file = filename
		
		characters += '\n'			

		view = VIEW.create_view(self.view,'error',self.edit,'Typescript : Errors List',characters)
		view.setup(files,points)		


# COMPILE VIEW
class TypescriptBuild(sublime_plugin.TextCommand):

	def run(self, edit, characters):
		if TSS.get_process(self.view) == None:
			MESSAGE.show('You must wait for the initialisation to finish')
			return

		self.window = sublime.active_window()
		if characters != False: self.window.run_command('save')

		filename = self.view.file_name()
		compiler = Compiler(self.window,get_root(),filename)
		compiler.daemon = True
		compiler.start()
		
		sublime.status_message('Compiling : '+filename)
			

class TypescriptBuildView(sublime_plugin.TextCommand):
	
	def run(self, edit, filename):
		window = sublime.active_window()
		settings = sublime.load_settings('T3S.sublime-settings')
		
		if filename != 'error':
			if settings.get('show_build_file'):
				if os.path.exists(filename):
					data = get_data(filename)
					VIEW.create_view(self.view,'compile',edit,'Typescript : Built File',data)
				else:
					VIEW.create_view(self.view,'compile',edit,'Typescript : Built File',filename)
		else:
			window.run_command("typescript_error_panel")