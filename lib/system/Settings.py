# coding=utf8

import sublime
import sys
import os

from .Liste import LISTE
from .Project import ProjectSettings, ProjectError
from ..Utils import read_and_decode_json_file, read_file

# ----------------------------------------- CONSTANT ---------------------------------------- #

SUBLIME_PROJECT = 'sublime_project'
SUBLIME_TS = 'sublime_ts'
NO_PROJECT = 'no_project'


# ----------------------------------------- SETTINGS ---------------------------------------- #
class Settings(object):

	projects_type = {}


	def __init__(self):
		super(Settings, self).__init__()


	def get(self,token):
		view = sublime.active_window().active_view()
		return self.projects_type[LISTE.get_root(view.file_name())].get(view,token)


	def get_node(self):
		view = sublime.active_window().active_view()
		node_path = self.projects_type[LISTE.get_root(view.file_name())].get(view,'node_path')
		if node_path == 'none':
			return '/usr/local/bin/node' if sys.platform == "darwin" else 'node'
		else:
			return node_path+'/node'


	def get_root(self,view):
		if view.file_name() == None: return 'no_ts'
		project_settings = view.settings().get('typescript')
		current_folder = os.path.dirname(view.file_name())
		top_folder =  self.get_top_folder(current_folder)
		top_folder_segments = top_folder.split(os.sep)
		has_project_settings = project_settings != None and hasattr(project_settings, 'get')

		# DO WE HAVE ROOT FILES DEFINED INSIDE THE PROJECT FILE
		if has_project_settings:
			roots = project_settings.get('roots')
			for root in roots:
				root_path = os.sep.join(top_folder_segments[:len(top_folder_segments)-1]+root.replace('\\','/').split('/'))
				root_top_folder = self.get_top_folder(os.path.dirname(root_path))
				if current_folder.lower().startswith(root_top_folder.lower()):
					if root_path not in self.projects_type: 
						self.projects_type[root_path] = ProjectSettings(SUBLIME_PROJECT)

					return root_path
				
		# PROJECT SETTINGS BUT NO ROOTS INSIDE > DO WE HAVE A SUBLIMETS FILE ?
		segments = current_folder.split(os.sep)
		segments[0] = top_folder.split(os.sep)[0]
		length = len(segments)
		segment_range =reversed(range(0,length+1))

		for index in segment_range:
			folder = os.sep.join(segments[:index])
			config_file = os.path.join(folder,'.sublimets')
			config_data = read_and_decode_json_file(config_file)
			if config_data != None:
				root_path = os.path.join(folder,config_data['root'])
				data = read_file(root_path) 
				if data != None:
					if root_path not in self.projects_type: 
						self.projects_type[root_path] = ProjectSettings(SUBLIME_TS,config_file)

					return root_path

				ProjectError(SUBLIME_TS,[config_data['root']+' is not a valid root file',config_file],config_file)
				return None

		error_type = SUBLIME_PROJECT if has_project_settings else NO_PROJECT
		path = sublime.active_window().project_file_name() if has_project_settings else None
		message = ['No valid root file for this project inside your project file',path] if has_project_settings else ['You didn\'t create a project file, please create one:','Choose between the three possibilities bellow :']
		ProjectError(error_type,message,path)
		return None
		

	def get_top_folder(self,current_folder):
		top_folder = None
		open_folders = sublime.active_window().folders()
		for folder in open_folders:
			if current_folder.lower().startswith(folder.lower()):
				top_folder = folder
				break

		if top_folder != None:
			return top_folder
		
		return current_folder
		

# ------------------------------------------- INIT ------------------------------------------- #

SETTINGS = Settings()
