# coding=utf8

from threading import Thread
import sublime
import re
import os

from ..Utils import get_data
from ..Tss import TSS
from .Liste import LISTE


# --------------------------------------- FILES -------------------------------------- #

class Files(object):

	def init(self,root):
		files = TSS.files(root)
		for f in files:
			self.add(root,f)


	def add(self,root,filename):
		LISTE.add(filename.replace('\\','/').lower(),{'root':root,'file':filename,'refs':self._get_references(get_data(filename))})


	def remove_by(self,root):
		LISTE.remove_by(root)


	def update(self,view,unused=False):
		filename = view.file_name().replace('\\','/')
		current_refs = LISTE.get(filename.lower())['refs']
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
			if get_data(LISTE.get(f)['file']) == None:
				to_delete.append(f)
		
		if len(to_delete)>0:
			self._reload(filename)
			for f in to_delete:
				LISTE.remove(f)


	def _add_ref(self,ref,filename,unused=False):
		(path,name) = os.path.split(filename)
		ref_path = os.path.abspath(path+'/'+ref)
		content = get_data(ref_path)
		if content != None:
			LISTE.get(filename.lower())['refs'].append(ref)
			sublime.active_window().run_command('save_all')
			self._reload(filename)
		else:
			if unused: self._reload(filename)


	def _remove_unused_ref(self,view,filename):
		refs = LISTE.get(filename.lower())['refs']
		file_refs =  self._get_references(view.substr(sublime.Region(0, view.size())))
		for ref in refs:
			if ref not in file_refs:
				LISTE.get(filename.lower())['refs'].remove(ref)



	def _get_references(self,content):
		if content == None: return
		refs = [ref[1:-1] for ref in re.findall("/// *<reference path *\=('.*?'|\".*?\")", content)]
		return refs


	def _reload(self,filename):
		reload = ReloadReference(filename)
		reload.daemon = True
		reload.start()

# -------------------------------------- RELOAD REF ---------------------------------- #

class ReloadReference(Thread):

	def __init__(self,filename):
		self.filename = filename
		Thread.__init__(self)
	
	def run(self):
		TSS.reload(self.filename,True)


# ----------------------------------- INITIALISATION --------------------------------- #

FILES = Files()
