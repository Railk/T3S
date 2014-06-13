# coding=utf8

from ..Utils import fn2k

class Liste(object):
	"""
	Liste keeps track of which file belongs to which rootfile. 
	The global LISTE is managed by FILES, which uses the tss 'files' command

	Format of self.liste =
	 { "/home/lowercased/file/path.ts" : 
			{ "refs" : [], root : "root file path", file : "/home/NOT/lowercased/file/path.ts" }
	 }

	"""

	liste = {}

	def get_root(self,filename):
		""" return <root filename> of file <filename> or None """
		if not filename or not self.has(filename):
			return None
		return self.liste[fn2k(filename)]['root']

	def get(self,filename):
		""" returns the { "refs": [], "root": , "file": } dictionary for filename """
		return self.liste[fn2k(filename)]

	def has(self,filename):
		""" returns weather or not this instance contains filename """
		return fn2k(filename) in self.liste

	def add(self,filename,data):
		""" adds or updates the dict for filename """
		self.liste[fn2k(filename)] = data

	def remove(self,filename):
		""" removes filename from list """
		del self.liste[fn2k(filename)]

	def remove_by_root(self, root_filename):
		""" remove all files which have this file as root file """
		to_delete = [file for file in self.file if self.get_root(file) == root_filename]

		for file in to_delete:
			del self.liste[file]

# global
LISTE = Liste()

def get_root(filename):
	return LISTE.get_root(filename)
