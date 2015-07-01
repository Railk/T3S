# coding=utf8

from subprocess import Popen, PIPE

import sublime
import os
import json

from ..Utils import dirname, read_and_decode_json_file, get_kwargs, ST3


# ------------------------------------- PROJECT SETTINGS ---------------------------------------- #

class ProjectSettings(object):

	def __init__(self,type,file=None):
		super(ProjectSettings, self).__init__()
		self.type = type
		self.file =  file

	def get(self,view,token):
		if self.file != None:
			config_data = read_and_decode_json_file(self.file)
			if 'settings' in config_data:
				return config_data['settings'][token]
			else:
				return self._default(token)
		else:
			ts = view.settings().get('typescript')
			if 'settings' in ts:
				if token in ts['settings']:
					return ts['settings'][token]
				print('Missing setting ["typescript"]["settings"]["%s"] in your config. Using Default: %s'
						% (token, str(self._default(token)) ) )

			return self._default(token)

	def _default(self,token):
		return sublime.load_settings('T3S.sublime-settings').get(token)


# ------------------------------------- PROJECT ERROR ----------------------------------------- #

class ProjectError(object):

	num_root_files = 1
	root_files_name = []
	create_project_type = ""
	project_name = ""
	folder_name = ""

	def __init__(self, kind, message, path):
		super(ProjectError, self).__init__()
		self.window = sublime.active_window()
		self.path = path
		self.kind = kind

		self.show(message,kind)


	def show(self,message,kind):
		self.messages = []
		self.messages.append(message)
		self.window.run_command("hide_overlay")

		if self.kind == 'sublime_ts':
			self.messages.append(['Open your .sublimets and Edit it','Click here to open the file'])
			self.messages.append(['Show me a .sublimets example','Click here to open the example file'])
			self.window.show_quick_panel(self.messages,self._on_done)
		elif self.kind == 'sublime_project':
			self.messages.append(['Open your project-file and Edit it','Click here to open the file'])
			self.messages.append(['Show me a project-file example','Click here to open the example file'])
			self.window.show_quick_panel(self.messages,self._on_done)
		elif self.kind == 'no_project':
			self.messages.append(['Create a sublime project-file (one or multiple root files)','Click here and follow the instructions'])
			self.messages.append(['Create a .sublimets project file (one root file only)','Click here and follow the instructions'])
			self.messages.append(['I don\'t understand please show me the README file','Click here to open the README.md file'])
			self.window.show_quick_panel(self.messages,self._on_create_project)


	def _on_done(self,index):
		if index==-1 or index==0:
			self.window.run_command("hide_overlay")
			return
		elif index == 1 :
			self.window.open_file(self.path)
		else:
			if self.kind == 'sublime_ts':
				self.window.open_file(dirname+'/examples/sublimets/.sublimets')
			elif self.kind == 'sublime_project':
				self.window.open_file(dirname+'/examples/sublimeproject/project.sublime-project')


	# BEGIN CREATING PROJECT
	def _on_create_project(self,index):
		if index == -1 or index == 0:
			self.window.run_command("hide_overlay")
			return
		elif index == 1:
			self.create_project_type = 'sublime_project'
			self.window.show_input_panel("Enter a name for your project file", "", self._set_project_name, None, None)
		elif index == 2:
			self.create_project_type = 'sublime_ts'
			self.window.show_input_panel("Enter the root file name", "", self._set_root_file_name, None, None)
			pass
		elif index == 3:
			self.window.open_file(dirname+'/README.md')


	# SET PROJECT NAME
	def _set_project_name(self,name):
		self.project_name = name
		self.window.show_input_panel("Enter the number of root files you want to include", "", self._set_num_root_file, None, None)


	# SET ROOT FILE NUMBER
	def _set_num_root_file(self,number):
		self.num_root_files = int(number)
		self.window.show_input_panel("Enter the first root file path (from top folder to your file)", "", self._set_root_file_name, None, None)


	# SET ROOT FILE
	def _set_root_file_name(self,name):
		self.root_files_name.append(name)

		if self.num_root_files == 1:
			if self.create_project_type == 'sublime_project':
				self.window.show_input_panel("Do you want to add project settings : yes | no", "", self._add_project_settings, None, None)
			else:
				(path, name) =  os.path.split(sublime.active_window().active_view().file_name())
				self.folder_name = path
				self.window.show_input_panel("Enter the folder path of your root file", path, self._set_folder_path, None, None)
		else:
			self.window.show_input_panel("Enter the next root file path (from top folder to your file)", "", self._set_root_file_name, None, None)

		self.num_root_files = self.num_root_files-1


	# SET FOLDER NAME
	def _set_folder_path(self,folder):
		if not os.path.isdir(folder):
			self.window.run_command("hide_overlay")
			sublime.status_message('the folder doesn\'t exist, try again')
			self.window.show_input_panel("Enter the folder path of your root file", self.folder_name, self._set_folder_path, None, None)
			return

		self.folder_name = folder
		self.window.show_input_panel("Do you want to add project settings : yes | no ", "", self._add_project_settings, None, None)


	# ADD PROJECTS SETTINGS
	def _add_project_settings(self,settings):
		settings = True if settings == 'yes' else False
		if self.create_project_type == 'sublime_project':
			self._create_sublime_project(settings)
		else:
			self._create_sublimets(settings)


	# CREATE SUBLIMETS
	def _create_sublimets(self,settings):
		if settings:
			content = json.dumps({"root":self.root_files_name[0],"settings":self._get_settings()}, sort_keys=True, indent=4)
		else:
			content = json.dumps({"root":self.root_files_name[0]}, sort_keys=False, indent=4)

		path = os.path.abspath(self.folder_name+'/.sublimets')
		self._create_project_file(content,path)
		self.window.open_file(path)
		self.window.run_command("hide_overlay")


	# CREATE SUBLIME-PROJECT
	def _create_sublime_project(self,settings):
		if settings:
			content = json.dumps({"folders":self._get_project_folders(),"settings":{"typescript":{"roots":self.root_files_name,"settings":self._get_settings()}}}, sort_keys=True, indent=4)
		else:
			content = json.dumps({"folders":self._get_project_folders(),"settings":{"typescript":{"roots":self.root_files_name}}}, sort_keys=False, indent=4)

		path =  os.path.abspath(self._get_top_folder(os.path.dirname(self.window.active_view().file_name())) +'/'+ self.project_name + '.sublime-project')
		self._create_project_file(content,path)
		self.window.open_file(path)
		self.window.run_command("hide_overlay")
		self._open_project(path)


	# CREATE PROJECT FILE
	def _create_project_file(self,content,path):
		file_ref = open(path, "w")
		file_ref.write(content);
		file_ref.close()


	# OPEN PROJECT
	def _open_project(self,path):
		kwargs = get_kwargs()
		if os.name == 'nt':
			os.chdir(self._get_sublime_path())
			Popen(['sublime_text.exe','--project',path], stdin=PIPE, stdout=PIPE, **kwargs)
		else:
			Popen([''+self._get_sublime_path()+'','--project',path], stdin=PIPE, stdout=PIPE, **kwargs)


	# GET PROJECT FOLDERS
	def _get_project_folders(self):
		folders = sublime.active_window().folders()
		folders.append(".")

		result = []
		for folder in folders:
			result.append({"follow_symlinks": True,"path":folder})

		return result


	# GET TOP FOLDER
	def _get_top_folder(self,current_folder):
		top_folder = None
		open_folders = sublime.active_window().folders()
		for folder in open_folders:
			if current_folder.lower().startswith(folder.lower()):
				top_folder = folder
				break

		if top_folder != None:
			return top_folder

		return current_folder


	# PARSE SETTINGS
	def _get_settings(self):
		settings = sublime.load_settings('T3S.sublime-settings')
		return {
			"auto_complete" : settings.get('auto_complete'),
			"node_path" : settings.get('node_path'),
			"error_on_save_only" : settings.get('error_on_save_only'),
			"build_on_save" : settings.get('build_on_save'),
			"show_build_file" : settings.get('show_build_file'),
			"build_parameters" : settings.get('build_parameters')
		}


	# GET SUBLIME PATH
	def _get_sublime_path(self):
		if sublime.platform() == 'osx':
			if ST3:
				return '/Applications/Sublime Text 3.app/Contents/SharedSupport/bin/subl'
			else:
				return '/Applications/Sublime Text 2.app/Contents/SharedSupport/bin/subl'
		elif sublime.platform() == 'linux':
			return open('/proc/self/cmdline').read().split(chr(0))[0]
		else:
			return os.path.abspath(os.path.join(dirname,'..','..','..'))
