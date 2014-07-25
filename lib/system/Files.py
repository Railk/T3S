# coding=utf8

from threading import Thread
import sublime
import re
import os

from ..Utils import read_file, file_exists, fn2l, Debug, max_calls
from ..Tss import TSS
from .Liste import LISTE


# --------------------------------------- FILES -------------------------------------- #

class Files(object):
	"""
		Keeps track of the files TSS uses (currently?).
		Keeps references like this /// <reference path="lib/mocha/mocha.d.ts" />
		up to date. For this it parses unsaved views after each keystroke.
	"""

	@max_calls(name='Files.init')
	def init(self, root, callback):
		self.update_indexed_files(root, callback)

	@max_calls(name='Files.update_indexed_files')
	def update_indexed_files(self, root, callback=None):
		""" add the files in current project (=root) determined by tss>files command to LISTE """
		def async_react(files):
			""" callback for async tss>files response. Add files"""
			for f in files:
				self.add(root, f)
			if callback is not None:
				callback()
		Debug('files', "GETTING FILE LIST from TSS")
		TSS.get_tss_indexed_files(root, async_react)


	@max_calls(name='Files.add')
	def add(self, root, filename):
		""" Adds/updates filename in LISTE, keeping track of belonging project (=root) and references """
		Debug('files', "ADD FILE to LISTE, parse references: %s" % filename)

		LISTE.add(filename,
			{'root' : root,
			 'file' : filename,
			 'refs' : self._get_references( read_file(filename) ) }
			 )


	def remove_by_root(self,root):
		""" remove all files belonging to project (=root) from LISTE """
		Debug('tss+', "Deleting the file<->rootfile associations for the just closing project %s" % root)
		LISTE.remove_by_root(root)

	@max_calls(name='Files.update')
	def update(self, filename, num_lines, content, remove_unused=False):
		""" 
			updates the references list in LISTE with the used references in the unsaved source file
			Also removes not existing files from LISTE	
		"""
		self.need_reload = False

		Debug('files', "UPDATE(remove_unused=%s) refs from %s" % (remove_unused, filename) )

		if not LISTE.has(filename):
			return

		tracked_refs = LISTE.get(filename)['refs']
		used_refs = self._get_references(content)

		if remove_unused:
			self._remove_unused_ref(tracked_refs, used_refs)

		self._add_missing_refs(tracked_refs, used_refs, filename, remove_unused)

		self._remove_non_existing_files()

		if self.need_reload:
			self._reload(filename)


	# TODO: should this one remove non existing REFs?
	def _remove_non_existing_files(self):
		to_delete = [f for f in LISTE.liste if not file_exists(LISTE.get(f)['file'])]
		if len(to_delete) > 0:
			self.need_reload = True
			for f in to_delete:
				Debug('files', "REMOVE file from LISTE: %s" % (str(f)[0:80], ))
				LISTE.remove(f)

	def _remove_unused_ref(self, tracked_refs, used_refs):
		for t_ref in list(tracked_refs):
			if t_ref not in used_refs:
				Debug('files', "REMOVED UNUSED reference %s from file xyz" % t_ref)
				tracked_refs.remove(t_ref)

	def _add_missing_refs(self, tracked_refs, used_refs, filename, remove_unused):
		for u_ref in used_refs:
			if u_ref not in tracked_refs:
				self._add_ref(u_ref, filename, remove_unused)

	def _add_ref(self, ref, filename, remove_unused=False):
		""" checks for existence of ref file before adding it to LISTE[file][refs] """
		directory = os.path.dirname(filename)
		ref_absolute_path = os.path.abspath(os.path.join(directory, ref))
		if file_exists(ref_absolute_path):
			Debug('files', "ADDED NEW reference %s (file %s), save_all files" % (ref, filename))
			LISTE.get(filename)['refs'].append(ref)

			# TODO: why saving? tss>reload will work anyway because of the automatic tss>updates
			# Should this trigger restructuration?
			sublime.active_window().run_command('save_all') 

			self.need_reload = True
		else:
			Debug('files', "DID NOT ADDED NEW reference %s because it does not exists (file %s)" % (ref, filename))
			if remove_unused:
				self.need_reload = True


	def _get_references(self, content):
		"""
		parses the typescript /// <reference path='' /> statements and 
		returns a list with all referenced filenames
		"""
		if content == None: return
		refs = [ref[1:-1] for ref in re.findall("/// *<reference path *\=('.*?'|\".*?\")", content)]
		return refs


	def _reload(self, filename):
		""" reloads and trigger showErrors """
		Debug('files', "TRIGGER TSS RELOAD")
		TSS.reload(filename)
		


# ----------------------------------- INITIALISATION --------------------------------- #

FILES = Files()
