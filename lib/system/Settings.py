import sublime
import sys
import os

from .Liste import LISTE
from ..Utils import get_data


SUBLIME_PROJECT = 'sublime_project'
SUBLIME_TS = 'sublimets'

class Settings(object):

	projects_type = {}


	def __init__(self):
		super(Settings, self).__init__()


	def get(self,token):
		view = sublime.active_window().active_view()
		return self.projects_type[LISTE.get_root(view.file_name())].get(view,token)


	def get_all(self):
		return


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

		if project_settings != None:
			roots = project_settings.get('roots')
			for root in roots:
				root_path = os.sep.join(top_folder_segments[:len(top_folder_segments)-1]+root.replace('\\','/').split('/'))
				root_dir = os.path.dirname(root_path)
				if current_folder.lower().startswith(root_dir.lower()):
					if root_path not in self.projects_type: 
						self.projects_type[root_path] = ProjectSettings(SUBLIME_PROJECT)

					return root_path
				
			return None

		else:
			segments = current_folder.split(os.sep)
			segments[0] = top_folder.split(os.sep)[0]
			length = len(segments)
			segment_range =reversed(range(0,length+1))

			for index in segment_range:
				folder = os.sep.join(segments[:index])
				config_file = os.path.join(folder,'.sublimets')
				config_data = get_data(config_file,True)
				if config_data != None:
					root_path = os.path.join(folder,config_data['root'])
					if root_path not in self.projects_type: 
						self.projects_type[root_path] = ProjectSettings(SUBLIME_TS,config_file)

					return root_path

			return None


	def get_project_type(self):
		pass
		

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



class ProjectSettings(object):

	def __init__(self,type,file=None):
		super(ProjectSettings, self).__init__()
		self.type = type
		self.file =  file

	def get(self,view,token):
		if self.file != None:
			config_data = get_data(self.file,True)
			if 'settings' in config_data:
				return config_data['settings'][token]
			else:
				return self._default(token)
		else:
			ts = view.settings().get('typescript')
			if 'settings' in ts:
				return ts['settings'][token]
			else:
				return self._default(token)

	def _default(self,token):
		return sublime.load_settings('T3S.sublime-settings').get(token)





SETTINGS = Settings()