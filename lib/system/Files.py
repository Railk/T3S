# coding=utf8

from threading import Thread
import sublime
import re
import os

from ..Utils import read_file, fn2l
from ..Tss import TSS
from .Liste import LISTE


# --------------------------------------- FILES -------------------------------------- #

class Files(object):
""" TODO What does this class? """

	def init(self, root):
		""" add the files in current project (=root) determined by tss>files command to LISTE """
		def async_react(files):
			""" callback for async tss>files response. Add files"""
			for f in files:
				self.add(root, f)
		TSS.files(root, async_react)


	def add(self, root, filename):
		""" Adds/updates filename in LISTE, keeping track of belonging project (=root) and references """
		LISTE.add(filename,
			{'root' : root,
			 'file' : filename,
			 'refs' : self._get_references(read_file(filename))}
			 )


	def remove_by_root(self,root):
		""" remove all files belonging to project (=root) from LISTE """
		LISTE.remove_by_root(root)


	def update(self, view, unused=False):
		""" """
		filename = fn2l(view.file_name())
		current_refs = LISTE.get(filename)['refs']
		refs =  self._get_references(view.substr(sublime.Region(0, view.size())))

		#UNUSED REF ?
		if unused: self._remove_unused_ref(view,filename)

		# REF CHANGE
		for ref in refs:
			if ref not in current_refs:
				self._add_ref(ref,filename,unused)

		# A FILE HAS BEEN REMOVED ?
		to_delete = []
		for f in LISTE.liste:
			if read_file(LISTE.get(f)['file']) == None:
				to_delete.append(f)
		
		if len(to_delete)>0:
			self._reload(filename)
			for f in to_delete:
				LISTE.remove(f)


	def _add_ref(self, ref, filename, unused=False):
		(path,name) = os.path.split(filename)
		ref_path = os.path.abspath(path+'/'+ref)
		content = read_file(ref_path)
		if content != None:
			LISTE.get(filename)['refs'].append(ref)
			sublime.active_window().run_command('save_all')
			self._reload(filename)
		else:
			if unused: self._reload(filename)


	def _remove_unused_ref(self,view,filename):
		refs = LISTE.get(filename)['refs']
		file_refs =  self._get_references(view.substr(sublime.Region(0, view.size())))
		for ref in refs:
			if ref not in file_refs:
				LISTE.get(filename)['refs'].remove(ref)



	def _get_references(self,content):
		if content == None: return
		refs = [ref[1:-1] for ref in re.findall("/// *<reference path *\=('.*?'|\".*?\")", content)]
		return refs


	def _reload(self,filename):
		## reload will be async anyway, removed code for thread creation
		TSS.reload(self.filename) 
		


# ----------------------------------- INITIALISATION --------------------------------- #

FILES = Files()
