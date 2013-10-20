class Liste(object):

	liste = {}

	def get_root(self,filename):
		if filename.replace('\\','/').lower() not in self.liste: 
			return None

		return self.liste[filename.replace('\\','/').lower()]['root']


	def get(self,filename):
		return self.liste[filename]


	def add(self,filename,data):
		self.liste[filename] = data


	def remove(self,filename):
		del self.liste[filename]


	def remove_by(self,filename):
		to_delete = []
		for file in self.liste:
			if self.liste[file]['root'] == filename:
				to_delete.append(file)

		for file in to_delete:
			del self.liste[file]


	def has(self,filename):
		return filename.replace('\\','/').lower() in self.liste


LISTE = Liste()